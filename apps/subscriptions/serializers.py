from rest_framework import serializers

from .models import ActivityPrice, Subscription


class ActivityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityPrice
        fields = ["id", "name", "price_real"]


class SubscriptionSerializer(serializers.ModelSerializer):
    included_activities = ActivityPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "name", "description", "included_activities", "perks",
            "price_real", "price_currency", "duration_days",
        ]