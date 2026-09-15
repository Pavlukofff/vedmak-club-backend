from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import TaskAssignment, TaskTemplate
from .serializers import (
    TaskAssignmentCreateSerializer,
    TaskAssignmentSerializer,
    TaskAssignmentUpdateSerializer,
    TaskTemplateSerializer,
)


def can_manage_tasks(user):
    return user.is_superuser or user.has_perm("tasks.can_manage_tasks")


class TaskTemplateListView(generics.ListAPIView):
    """Доска объявлений с квестами — публичная, как доска в самом клубе."""

    queryset = TaskTemplate.objects.filter(is_active=True)
    serializer_class = TaskTemplateSerializer
    permission_classes = [permissions.AllowAny]


class TaskTemplateDetailView(generics.RetrieveAPIView):
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [permissions.AllowAny]


class TaskAssignmentListCreateView(generics.ListCreateAPIView):
    """Раздел 4.12 плана.

    GET: обычный участник видит только свои задания; роль с can_manage_tasks
    видит все, с фильтром ?user=<username>.
    POST: «взять задание» — самообслуживание, target по умолчанию — сам
    пользователь; can_manage_tasks может выдать задание другому.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return TaskAssignmentCreateSerializer if self.request.method == "POST" else TaskAssignmentSerializer

    def get_queryset(self):
        qs = TaskAssignment.objects.select_related("task_template", "user")
        requester = self.request.user
        if can_manage_tasks(requester):
            username = self.request.query_params.get("user")
            return qs.filter(user__username=username) if username else qs
        return qs.filter(user=requester)

    def perform_create(self, serializer):
        requester = self.request.user
        target_user = serializer.validated_data.get("user")

        if target_user and target_user != requester and not can_manage_tasks(requester):
            raise PermissionDenied("Можно взять задание только для себя.")
        target_user = target_user or requester

        template = serializer.validated_data["task_template"]

        if not template.is_repeatable and TaskAssignment.objects.filter(
            task_template=template, user=target_user,
        ).exists():
            raise ValidationError("Это задание нельзя брать повторно.")

        if template.max_slots is not None and template.available_slots <= 0:
            raise ValidationError("Нет свободных копий этого задания.")

        serializer.save(user=target_user)


class TaskAssignmentDetailView(generics.RetrieveUpdateAPIView):
    """GET — владелец или can_manage_tasks. PATCH статуса:

    владелец может только отказаться от своего задания в процессе
    (status=cancelled); can_manage_tasks — любой переход («принудительно
    закрыть/отменить», в т.ч. подтвердить выполнение с начислением награды).
    """

    queryset = TaskAssignment.objects.select_related("task_template", "user")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return TaskAssignmentUpdateSerializer if self.request.method in ("PUT", "PATCH") else TaskAssignmentSerializer

    def get_object(self):
        obj = super().get_object()
        requester = self.request.user
        if obj.user_id != requester.id and not can_manage_tasks(requester):
            raise PermissionDenied("Это не ваше задание.")
        return obj

    def perform_update(self, serializer):
        requester = self.request.user
        instance = serializer.instance

        if not can_manage_tasks(requester):
            new_status = serializer.validated_data.get("status", instance.status)
            if new_status != TaskAssignment.Status.CANCELLED:
                raise PermissionDenied("Можно только отказаться от задания.")
            if instance.status != TaskAssignment.Status.IN_PROGRESS:
                raise ValidationError("Отказаться можно только от задания в процессе выполнения.")

        instance._closed_by = requester
        serializer.save()