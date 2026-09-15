from rest_framework import serializers

from apps.accounts.models import User

from .models import EffectType, ItemEffect, Purchase, ShopItem


class EffectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EffectType
        fields = ["id", "code", "name", "description"]


class ItemEffectSerializer(serializers.ModelSerializer):
    type = EffectTypeSerializer(read_only=True)

    class Meta:
        model = ItemEffect
        fields = ["id", "type", "value", "duration", "duration_value"]


class ShopItemSerializer(serializers.ModelSerializer):
    """Карточка товара — раздел 4.8 плана."""

    min_rank = serializers.SlugRelatedField(slug_field="name", read_only=True)
    effects = ItemEffectSerializer(many=True, read_only=True)

    class Meta:
        model = ShopItem
        fields = [
            "id", "name", "category", "price", "description", "image", "stock",
            "min_rank", "toxicity", "effects",
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    """Чтение — «Мои покупки / инвентарь»."""

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    item = ShopItemSerializer(read_only=True)
    granted_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Purchase
        fields = [
            "id", "user", "item", "price_paid", "granted_by",
            "purchased_at", "is_used", "used_at",
        ]
        read_only_fields = fields


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """«Купить» / «выдать» товар. user необязателен — по умолчанию себе;

    указать другого пользователя или получить бесплатную выдачу может
    только роль с can_grant_items (проверяется во view).
    """

    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(is_active=True))
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False,
    )

    class Meta:
        model = Purchase
        fields = ["id", "item", "user"]


class PurchaseUpdateSerializer(serializers.ModelSerializer):
    """Отметить предмет использованным (необратимо)."""

    class Meta:
        model = Purchase
        fields = ["id", "is_used", "used_at"]
        read_only_fields = ["id", "used_at"]

    def validate_is_used(self, value):
        if self.instance and self.instance.is_used and not value:
            raise serializers.ValidationError("Нельзя отменить отметку об использовании.")
        return value