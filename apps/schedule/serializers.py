from rest_framework import serializers

from apps.subscriptions.models import ActivityPrice

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    activity = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = ScheduleEntry
        fields = [
            "id", "weekday", "start_time", "end_time", "title",
            "activity", "location", "notes",
        ]


class ScheduleEntryWriteSerializer(serializers.ModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(
        queryset=ActivityPrice.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = ScheduleEntry
        fields = [
            "id", "weekday", "start_time", "end_time", "title",
            "activity", "location", "notes", "is_active",
        ]
