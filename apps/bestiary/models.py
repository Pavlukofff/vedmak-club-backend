from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone


class Bestiary(models.Model):
    """Справочник видов монстров — раздел 4.7 плана.

    Статичная энциклопедия (описание, категория, опасность), отдельно от
    журнала охот (MonsterKill).
    """

    class DangerLevel(models.TextChoices):
        LOW = "low", "Низкая"
        MEDIUM = "medium", "Средняя"
        HIGH = "high", "Высокая"
        DEADLY = "deadly", "Смертельная"

    name = models.CharField("название", max_length=150, unique=True)
    category = models.CharField(
        "категория", max_length=100, blank=True,
        help_text="Например: низший вид / реликт / гибрид / проклятье",
    )
    danger_level = models.CharField(
        "уровень опасности", max_length=10, choices=DangerLevel.choices,
    )
    description = models.TextField("описание", blank=True)
    image = models.ImageField("изображение", upload_to="bestiary/", blank=True, null=True)

    class Meta:
        verbose_name = "вид бестиария"
        verbose_name_plural = "бестиарий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MonsterKill(models.Model):
    """Запись журнала охот — раздел 4.7 плана.

    Создаётся только админом/судьёй по итогам боя/охоты, без самозаявления
    пользователем. Начисление награды (опыт/кроны) — тоже вручную, тем же
    или другим уполномоченным лицом: при переходе reward_granted False→True
    суммы reward_experience/reward_currency сразу прибавляются пользователю.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="monster_kills", on_delete=models.PROTECT,
    )
    bestiary = models.ForeignKey(
        Bestiary, verbose_name="вид монстра",
        related_name="kills", on_delete=models.PROTECT,
    )
    battle = models.ForeignKey(
        "battles.Battle", verbose_name="бой",
        related_name="monster_kills", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Если убийство произошло в рамках боя/охоты",
    )
    date = models.DateTimeField("дата", default=timezone.now)
    notes = models.TextField("заметки", blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто зафиксировал",
        related_name="monster_kills_recorded", on_delete=models.PROTECT,
    )

    reward_granted = models.BooleanField("награда начислена", default=False)
    reward_granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто начислил награду",
        related_name="monster_kill_rewards_granted", blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    reward_experience = models.PositiveIntegerField("награда: опыт", blank=True, null=True)
    reward_currency = models.PositiveIntegerField("награда: кроны", blank=True, null=True)

    class Meta:
        verbose_name = "убитый монстр"
        verbose_name_plural = "убитые монстры"
        ordering = ["-date"]
        permissions = [
            ("can_record_kills", "Может фиксировать убийства монстров и начислять награды"),
        ]

    def __str__(self):
        return f"{self.user} убил(а) {self.bestiary}"

    def save(self, *args, **kwargs):
        granting_now = self.reward_granted
        if self.pk:
            previously_granted = MonsterKill.objects.filter(pk=self.pk).values_list(
                "reward_granted", flat=True,
            ).first()
            granting_now = self.reward_granted and not previously_granted

        super().save(*args, **kwargs)

        if granting_now and (self.reward_experience or self.reward_currency):
            update_fields = []
            if self.reward_experience:
                self.user.experience = F("experience") + self.reward_experience
                update_fields.append("experience")
            if self.reward_currency:
                self.user.balance = F("balance") + self.reward_currency
                update_fields.append("balance")
            self.user._activity_actor = self.reward_granted_by
            self.user.save(update_fields=update_fields)