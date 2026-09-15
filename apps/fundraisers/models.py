from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Fundraiser(models.Model):
    """Сбор средств — раздел 1 плана («список активных и завершённых,

    прогресс-бар»). Своей схемы в разделе 4 плана нет — спроектирован по
    аналогии с уже готовыми моделями. Цена в реальных деньгах (BYN), как и
    абонементы/разовые активности — сайт не принимает оплату онлайн, взносы
    офлайновые и фиксируются вручную (см. FundraiserContribution).
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    cover_image = models.ImageField("изображение", upload_to="fundraisers/", blank=True, null=True)
    goal_amount = models.DecimalField("цель, BYN", max_digits=10, decimal_places=2)
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )
    start_date = models.DateField("дата начала", default=timezone.localdate)
    end_date = models.DateField("дата окончания", blank=True, null=True)

    class Meta:
        verbose_name = "сбор средств"
        verbose_name_plural = "сборы средств"
        ordering = ["-start_date"]
        permissions = [
            ("can_manage_fundraisers", "Может управлять сборами средств и фиксировать взносы"),
        ]

    def __str__(self):
        return self.title

    @property
    def raised_amount(self):
        total = self.contributions.aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0")

    @property
    def progress_percent(self):
        if not self.goal_amount:
            return 0.0
        return min(100.0, round(float(self.raised_amount) / float(self.goal_amount) * 100, 1))


class FundraiserContribution(models.Model):
    """Взнос — журнал, из которого считается raised_amount (без ручного

    поля, которое могло бы разойтись с реальностью). Фиксируется только
    уполномоченной ролью постфактум (офлайн-взнос — наличные/перевод),
    без самозаявления донатера, как и с боями/убийствами монстров.
    """

    fundraiser = models.ForeignKey(
        Fundraiser, verbose_name="сбор", related_name="contributions", on_delete=models.CASCADE,
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="участник клуба",
        related_name="fundraiser_contributions", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Если донатер — зарегистрированный участник клуба",
    )
    contributor_name = models.CharField(
        "имя донатера", max_length=150, blank=True,
        help_text="Для гостя/внешнего донатера без аккаунта на сайте",
    )
    amount = models.DecimalField("сумма, BYN", max_digits=10, decimal_places=2)
    is_anonymous = models.BooleanField("анонимный взнос", default=False)
    comment = models.TextField("комментарий", blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто зафиксировал",
        related_name="fundraiser_contributions_recorded", on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField("зафиксирован", auto_now_add=True)

    class Meta:
        verbose_name = "взнос"
        verbose_name_plural = "взносы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.amount} BYN — {self.fundraiser}"
