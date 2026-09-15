from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone


class TaskTemplate(models.Model):
    """Шаблон задания — раздел 4.12 плана.

    completions_count / available_slots — вычисляемые величины
    (не хранятся), как и описано в плане.
    """

    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    requirements = models.TextField(
        "требования", blank=True, help_text="Что нужно для взятия/выполнения квеста",
    )

    reward_experience = models.PositiveIntegerField("награда: опыт", default=0)
    reward_currency = models.PositiveIntegerField("награда: кроны", default=0)

    max_slots = models.PositiveIntegerField(
        "лимит одновременных копий", blank=True, null=True,
        help_text="Сколько одинаковых копий доступно одновременно; пусто = без лимита",
    )
    is_repeatable = models.BooleanField(
        "можно брать повторно", default=False,
        help_text="Может ли один пользователь брать это задание больше одного раза",
    )
    is_active = models.BooleanField("активно", default=True)

    class Meta:
        verbose_name = "задание"
        verbose_name_plural = "задания"
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def completions_count(self):
        return self.assignments.filter(status=TaskAssignment.Status.COMPLETED).count()

    @property
    def in_progress_count(self):
        return self.assignments.filter(status=TaskAssignment.Status.IN_PROGRESS).count()

    @property
    def available_slots(self):
        if self.max_slots is None:
            return None
        return max(0, self.max_slots - self.in_progress_count)


class TaskAssignment(models.Model):
    """Выданное задание — раздел 4.12 плана.

    Взятие задания — самообслуживание участника (аналог «взять свиток в
    руки», раздел 4.8). Принудительная смена статуса (закрыть/отменить/
    подтвердить выполнение) — только для роли с правом can_manage_tasks.
    При переходе в completed награда шаблона начисляется пользователю один
    раз (см. TaskAssignment.save()).
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Выполняется"
        COMPLETED = "completed", "Выполнено"
        FAILED = "failed", "Провалено"
        CANCELLED = "cancelled", "Отменено"

    task_template = models.ForeignKey(
        TaskTemplate, verbose_name="задание",
        related_name="assignments", on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="task_assignments", on_delete=models.CASCADE,
    )
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.IN_PROGRESS,
    )
    assigned_at = models.DateTimeField("взято", auto_now_add=True)
    completed_at = models.DateTimeField("завершено", blank=True, null=True)

    class Meta:
        verbose_name = "выданное задание"
        verbose_name_plural = "выданные задания"
        ordering = ["-assigned_at"]
        permissions = [
            ("can_manage_tasks", "Может выдавать/закрывать задания за других и менять статусы"),
        ]

    def __str__(self):
        return f"{self.user} — {self.task_template} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        completing_now = self.status == self.Status.COMPLETED
        if self.pk:
            previous_status = TaskAssignment.objects.filter(pk=self.pk).values_list(
                "status", flat=True,
            ).first()
            completing_now = self.status == self.Status.COMPLETED and previous_status != self.Status.COMPLETED

        if completing_now and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

        if completing_now:
            template = self.task_template
            update_fields = []
            if template.reward_experience:
                self.user.experience = F("experience") + template.reward_experience
                update_fields.append("experience")
            if template.reward_currency:
                self.user.balance = F("balance") + template.reward_currency
                update_fields.append("balance")
            if update_fields:
                self.user._activity_actor = getattr(self, "_closed_by", None)
                self.user.save(update_fields=update_fields)