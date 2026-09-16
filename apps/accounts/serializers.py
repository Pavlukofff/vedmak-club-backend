from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import AvatarPreset, CurrencyTransfer, DisplayNameChangeRequest, User


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация — раздел 4.1 плана."""

    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, label="Подтверждение пароля")
    agree_to_rules = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username", "email", "password", "password2",
            "display_name", "birth_date", "agree_to_rules",
        ]

    def validate_agree_to_rules(self, value):
        if not value:
            raise serializers.ValidationError("Нужно согласиться с правилами клуба.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        validated_data.pop("agree_to_rules")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AvatarPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvatarPreset
        fields = ["id", "title", "category", "image"]


class PublicRankSerializer(serializers.Serializer):
    name = serializers.CharField()
    icon = serializers.CharField()


class PublicProfileSerializer(serializers.ModelSerializer):
    """Публичный профиль — раздел 4.4 плана.

    Имя/фамилия и дата рождения отдаются только в соответствии с
    выбором самого пользователя (name_visibility / birth_date_visibility).
    """

    school = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    titles = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    birth_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "display_name", "avatar", "character_description",
            "school", "rank", "roles", "titles", "level", "experience",
            "first_name", "last_name", "birth_date",
        ]

    def get_school(self, obj):
        return obj.school.name if obj.school_id else None

    def get_rank(self, obj):
        if not obj.rank_id:
            return None
        return {"name": obj.rank.name, "icon": obj.rank.icon}

    def get_roles(self, obj):
        return list(obj.groups.values_list("name", flat=True))

    def get_titles(self, obj):
        return list(obj.title_awards.values_list("title__name", flat=True))

    def get_first_name(self, obj):
        return obj.first_name if obj.name_visibility == User.NameVisibility.PUBLIC else None

    def get_last_name(self, obj):
        return obj.last_name if obj.name_visibility == User.NameVisibility.PUBLIC else None

    def get_birth_date(self, obj):
        if not obj.birth_date:
            return None
        if obj.birth_date_visibility == User.BirthDateVisibility.FULL:
            return obj.birth_date.isoformat()
        if obj.birth_date_visibility == User.BirthDateVisibility.DAY_MONTH:
            return {"day": obj.birth_date.day, "month": obj.birth_date.month}
        return None


class PublicProfileDetailSerializer(PublicProfileSerializer):
    """Страница профиля (детальная) — добавляет статистику боёв, раздел 4.4 плана."""

    battle_stats = serializers.SerializerMethodField()

    class Meta(PublicProfileSerializer.Meta):
        fields = PublicProfileSerializer.Meta.fields + ["battle_stats"]

    def get_battle_stats(self, obj):
        from apps.battles.stats import battle_stats_for_user

        return battle_stats_for_user(obj)


class MeSerializer(serializers.ModelSerializer):
    """Личный кабинет — раздел 4.5 плана.

    displayName, школа и ранг здесь read-only: никнейм меняется только через
    DisplayNameChangeRequest, школу/ранг назначают админ/мастер вручную.
    """

    school = serializers.SerializerMethodField()
    rank = PublicRankSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "display_name", "email", "email_verified",
            "avatar", "school", "rank", "level", "experience", "balance",
            "first_name", "last_name", "name_visibility",
            "birth_date", "birth_date_visibility", "character_description",
            "is_staff",
        ]
        read_only_fields = [
            "id", "username", "display_name", "email", "email_verified",
            "avatar", "level", "experience", "balance", "is_staff",
        ]

    def get_school(self, obj):
        return obj.school.name if obj.school_id else None


class DisplayNameChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplayNameChangeRequest
        fields = [
            "id", "current_name", "requested_name", "reason",
            "status", "created_at", "reviewed_at",
        ]
        read_only_fields = ["id", "current_name", "status", "created_at", "reviewed_at"]

    def validate_requested_name(self, value):
        if User.objects.filter(display_name=value).exclude(pk=self.context["request"].user.pk).exists():
            raise serializers.ValidationError("Это имя уже занято.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return DisplayNameChangeRequest.objects.create(
            user=user, current_name=user.display_name, **validated_data,
        )


class CurrencyTransferSerializer(serializers.ModelSerializer):
    """Передача кронов любому пользователю — самообслуживание."""

    sender = serializers.SlugRelatedField(slug_field="username", read_only=True)
    recipient = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = CurrencyTransfer
        fields = ["id", "sender", "recipient", "amount", "message", "created_at"]
        read_only_fields = ["id", "sender", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        return value

    def validate(self, attrs):
        sender = self.context["request"].user
        recipient = attrs["recipient"]
        if recipient == sender:
            raise serializers.ValidationError("Нельзя перевести кроны самому себе.")
        if sender.balance < attrs["amount"]:
            raise serializers.ValidationError({"amount": "Недостаточно кронов на балансе."})
        return attrs
