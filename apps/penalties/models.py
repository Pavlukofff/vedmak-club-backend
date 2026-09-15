from django.conf import settings
from django.db import models


class Penalty(models.Model):
    """Взыскание — раздел 4.17 плана."""

    class Type(models.TextChoices):
        REMARK = "remark", "Замечание"
        BATTLE_REMARK = "battle_remark", "Боевое замечание"
        WARNING = "warning", "Предупреждение"
        BATTLE_SUSPENSION = "battle_suspension", "Временное отстранение от боёв"
        TEMP_BAN = "temp_ban", "Временный бан"
        CHARACTER_RESET = "character_reset", "Обнуление персонажа"
        PERMANENT_BAN = "permanent_ban", "Бессрочный бан"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        EXPIRED = "expired", "Сгорело"
        CANCELLED = "cancelled", "Отменено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="penalties", on_delete=models.CASCADE,
    )
    type = models.CharField("тип", max_length=20, choices=Type.choices)
    reason = models.TextField("причина")
    related_battle = models.ForeignKey(
        "battles.Battle", verbose_name="связанный бой",
        related_name="penalties", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Если взыскание вынесено по итогам конкретного боя",
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто вынес",
        related_name="issued_penalties", on_delete=models.PROTECT,
    )
    issued_at = models.DateTimeField("вынесено", auto_now_add=True)
    expires_at = models.DateTimeField(
        "сгорает", blank=True, null=True,
        help_text="Для авто-сгорания замечаний/предупреждений",
    )
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )

    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто отменил",
        related_name="cancelled_penalties", blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    cancel_reason = models.TextField("причина отмены", blank=True)
    cancelled_at = models.DateTimeField("отменено", blank=True, null=True)

    class Meta:
        verbose_name = "взыскание"
        verbose_name_plural = "взыскания"
        ordering = ["-issued_at"]
        permissions = [
            ("can_issue_penalties", "Может выносить взыскания"),
            ("can_cancel_penalties", "Может отменять взыскания"),
            ("can_view_penalties", "Может просматривать чужую историю взысканий"),
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.user} ({self.get_status_display()})"
