from rest_framework import serializers

from apps.accounts.models import User

from .models import TaskAssignment, TaskTemplate


class TaskTemplateSerializer(serializers.ModelSerializer):
    completions_count = serializers.IntegerField(read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = TaskTemplate
        fields = [
            "id", "title", "description", "requirements", "reward_experience", "reward_currency",
            "max_slots", "is_repeatable", "is_active", "completions_count", "available_slots",
        ]

    def get_available_slots(self, obj):
        return obj.available_slots


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Чтение — раздел 4.12 плана («Мои задания»)."""

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    task_template = TaskTemplateSerializer(read_only=True)

    class Meta:
        model = TaskAssignment
        fields = ["id", "task_template", "user", "status", "assigned_at", "completed_at"]
        read_only_fields = fields


class TaskAssignmentCreateSerializer(serializers.ModelSerializer):
    """«Взять задание». user необязателен — по умолчанию берущий сам себя;

    указать другого пользователя может только роль с can_manage_tasks
    (проверяется во view).
    """

    task_template = serializers.PrimaryKeyRelatedField(
        queryset=TaskTemplate.objects.filter(is_active=True),
    )
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False,
    )

    class Meta:
        model = TaskAssignment
        fields = ["id", "task_template", "user", "status", "assigned_at"]
        read_only_fields = ["id", "status", "assigned_at"]


class TaskAssignmentUpdateSerializer(serializers.ModelSerializer):
    """Смена статуса — раздел 4.12: «принудительно закрыть/отменить»."""

    class Meta:
        model = TaskAssignment
        fields = ["id", "status", "completed_at"]
        read_only_fields = ["id", "completed_at"]