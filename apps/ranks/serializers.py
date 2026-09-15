from rest_framework import serializers

from .models import Rank, RankRequirement, RankReward, RankUpRequest


class RankRequirementSerializer(serializers.ModelSerializer):
    target_rank = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = RankRequirement
        fields = ["id", "type", "value", "target_rank", "description"]


class RankRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankReward
        fields = ["id", "type", "value", "description"]


class RankSerializer(serializers.ModelSerializer):
    """Справочник рангов цеха — раздел 4.11 плана."""

    requirements = RankRequirementSerializer(many=True, read_only=True)
    rewards = RankRewardSerializer(many=True, read_only=True)

    class Meta:
        model = Rank
        fields = ["id", "name", "icon", "order", "requirements", "rewards"]


class RankBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ["id", "name", "icon", "order"]


class RankUpRequestSerializer(serializers.ModelSerializer):
    """Чтение заявки — раздел 4.11 плана."""

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    from_rank = RankBriefSerializer(read_only=True)
    to_rank = RankBriefSerializer(read_only=True)
    reviewed_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = RankUpRequest
        fields = [
            "id", "user", "from_rank", "to_rank", "status",
            "reviewed_by", "comment", "created_at", "reviewed_at",
        ]
        read_only_fields = fields


class RankUpRequestCreateSerializer(serializers.ModelSerializer):
    """«Подать заявку на ранг X» — раздел 4.11 плана.

    user/from_rank проставляются во view (текущий пользователь и его
    текущий ранг). to_rank обязан быть следующим по порядку рангом —
    заявки «через ступень» не допускаются.
    """

    to_rank = serializers.PrimaryKeyRelatedField(queryset=Rank.objects.all())

    class Meta:
        model = RankUpRequest
        fields = ["id", "to_rank", "comment"]

    def validate_to_rank(self, to_rank):
        user = self.context["request"].user
        current_rank = user.rank
        if current_rank is None:
            raise serializers.ValidationError("У вас ещё не назначен текущий ранг.")
        if to_rank.order != current_rank.order + 1:
            raise serializers.ValidationError(
                "Заявку можно подать только на следующий по порядку ранг.",
            )
        if RankUpRequest.objects.filter(
            user=user, status=RankUpRequest.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                "У вас уже есть заявка на рассмотрении.",
            )
        return to_rank