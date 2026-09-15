from rest_framework import serializers

from apps.accounts.models import User

from .models import Battle


class BattleSerializer(serializers.ModelSerializer):
    fighter1 = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    fighter2 = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    winner = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False, allow_null=True,
    )
    main_judge = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False, allow_null=True,
    )
    side_judge = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False, allow_null=True,
    )
    recorded_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Battle
        fields = [
            "id", "type", "fighter1", "fighter2", "winner",
            "main_judge", "side_judge", "is_ranked", "tournament", "date", "notes", "recorded_by",
        ]
        read_only_fields = ["recorded_by"]

    def validate(self, attrs):
        def current(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default) if self.instance else default

        fighter1 = current("fighter1")
        fighter2 = current("fighter2")
        winner = current("winner")
        is_ranked = current("is_ranked", False)
        main_judge = current("main_judge")

        if fighter1 and fighter2 and fighter1 == fighter2:
            raise serializers.ValidationError("Участники боя должны быть разными.")
        if winner and winner not in (fighter1, fighter2):
            raise serializers.ValidationError(
                {"winner": "Победитель должен быть одним из участников боя."},
            )
        if is_ranked and not main_judge:
            raise serializers.ValidationError(
                {"main_judge": "Для рангового/квестового боя обязателен главный судья."},
            )
        return attrs