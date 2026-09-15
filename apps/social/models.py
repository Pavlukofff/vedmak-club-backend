from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class SocialLink(models.Model):
    """Соц-сеть клуба/мастера/оружейни — раздел 4.16 плана."""

    class OwnerType(models.TextChoices):
        CLUB = "club", "Клуб"
        MASTER = "master", "Мастер школы"
        ARMORY = "armory", "Оружейня"

    owner_type = models.CharField("тип владельца", max_length=20, choices=OwnerType.choices)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="владелец",
        related_name="social_links", blank=True, null=True, on_delete=models.CASCADE,
        help_text="Заполняется, только если тип владельца — «Мастер школы»",
    )
    platform = models.CharField("платформа", max_length=100, help_text="Telegram, VK, Instagram и т.д.")
    url = models.URLField("ссылка")
    label = models.CharField("подпись", max_length=200, blank=True)

    class Meta:
        verbose_name = "ссылка на соц-сеть"
        verbose_name_plural = "ссылки на соц-сети"
        ordering = ["owner_type", "platform"]
        permissions = [
            ("can_manage_social_links", "Может управлять ссылками клуба/оружейни/других мастеров"),
        ]

    def __str__(self):
        return f"{self.get_owner_type_display()} — {self.platform}"

    def clean(self):
        if self.owner_type == self.OwnerType.MASTER and not self.owner_id:
            raise ValidationError("Для типа «Мастер школы» нужно указать владельца.")
        if self.owner_type != self.OwnerType.MASTER and self.owner_id:
            raise ValidationError("Владелец указывается только для типа «Мастер школы».")
