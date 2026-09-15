from rest_framework import serializers

from apps.accounts.models import User

from .models import SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = SocialLink
        fields = ["id", "owner_type", "owner", "platform", "url", "label"]


class SocialLinkWriteSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = SocialLink
        fields = ["id", "owner_type", "owner", "platform", "url", "label"]

    def validate(self, attrs):
        def current(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default) if self.instance else default

        owner_type = current("owner_type")
        owner = current("owner")

        if owner_type == SocialLink.OwnerType.MASTER and not owner:
            raise serializers.ValidationError(
                {"owner": "Для типа «Мастер школы» нужно указать владельца."},
            )
        if owner_type != SocialLink.OwnerType.MASTER and owner:
            raise serializers.ValidationError(
                {"owner": "Владелец указывается только для типа «Мастер школы»."},
            )
        return attrs
