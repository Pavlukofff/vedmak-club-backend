from rest_framework import serializers

from apps.accounts.models import User

from .models import Title, TitleAward


class TitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ["id", "name", "description"]


class TitleAwardSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    title = TitleSerializer(read_only=True)
    granted_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = TitleAward
        fields = ["id", "user", "title", "reason", "granted_by", "granted_at"]
        read_only_fields = fields


class TitleAwardCreateSerializer(serializers.ModelSerializer):
    """Выдать титул — раздел «Титулы»: только admin/can_grant_titles."""

    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    title = serializers.PrimaryKeyRelatedField(queryset=Title.objects.all())

    class Meta:
        model = TitleAward
        fields = ["id", "user", "title", "reason"]
