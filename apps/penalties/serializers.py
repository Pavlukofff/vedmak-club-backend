from rest_framework import serializers

from apps.accounts.models import User
from apps.battles.models import Battle

from .models import Penalty


class PenaltySerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    issued_by = serializers.SlugRelatedField(slug_field="username", read_only=True)
    cancelled_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Penalty
        fields = [
            "id", "user", "type", "reason", "related_battle", "issued_by", "issued_at",
            "expires_at", "status", "cancelled_by", "cancel_reason", "cancelled_at",
        ]
        read_only_fields = fields


class PenaltyIssueSerializer(serializers.ModelSerializer):
    """Форма «Вынести взыскание» — раздел 4.17 плана. issued_by проставляется во view."""

    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    related_battle = serializers.PrimaryKeyRelatedField(
        queryset=Battle.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = Penalty
        fields = ["id", "user", "type", "reason", "related_battle", "expires_at"]


class PenaltyCancelSerializer(serializers.Serializer):
    cancel_reason = serializers.CharField()
