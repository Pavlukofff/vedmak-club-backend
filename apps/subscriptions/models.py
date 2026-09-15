from django.db import models


class ActivityPrice(models.Model):
    """Разовое занятие без абонемента — раздел 4.10 плана. Цена в реальных деньгах (BYN)."""

    name = models.CharField("название", max_length=150, unique=True)
    price_real = models.DecimalField("цена, BYN", max_digits=8, decimal_places=2)
    is_active = models.BooleanField("активна", default=True)

    class Meta:
        verbose_name = "разовая активность"
        verbose_name_plural = "разовые активности"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Абонемент-билет — раздел 4.10 плана.

    На старте — только витрина (список с описанием и ценой), без встроенной
    оплаты: интеграция с реальным эквайрингом не нужна.
    """

    name = models.CharField("название", max_length=150, unique=True)
    description = models.TextField("описание", blank=True)
    included_activities = models.ManyToManyField(
        ActivityPrice, verbose_name="включённые активности",
        related_name="subscriptions", blank=True,
    )
    perks = models.TextField(
        "привилегии", blank=True,
        help_text="Произвольные привилегии: приоритетная запись, гарантированные слоты, гость и т.д.",
    )
    price_real = models.DecimalField("цена, BYN", max_digits=8, decimal_places=2)
    price_currency = models.PositiveIntegerField(
        "цена, кроны", blank=True, null=True, help_text="Стоимость в кронах — опционально",
    )
    duration_days = models.PositiveIntegerField("срок действия, дней")
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "абонемент"
        verbose_name_plural = "абонементы"
        ordering = ["price_real"]

    def __str__(self):
        return self.name