from rest_framework import serializers

from .models import ActivityLogEntry


class ActivityLogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.SlugRelatedField(slug_field="username", read_only=True)
    target = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = ActivityLogEntry
        fields = ["id", "type", "actor", "target", "related_object_id", "message", "created_at"]


class BirthdaySerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username")
    display_name = serializers.CharField(source="user.display_name")
    next_birthday = serializers.DateField()
    days_until = serializers.IntegerField()
