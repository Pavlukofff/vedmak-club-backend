from rest_framework import serializers

from .models import ClubCodex


class ClubCodexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubCodex
        fields = ["content", "updated_at"]
