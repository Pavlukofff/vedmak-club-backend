from django.conf import settings
from django.db import models


class Title(models.Model):
    """Каталог титулов — просто слово (или короткая фраза) с общим описанием,

    что оно означает. Выдача конкретному пользователю — TitleAward ниже.
    """

    name = models.CharField("название", max_length=100, unique=True)
    description = models.TextField("описание", blank=True, help_text="Что в общем означает этот титул")

    class Meta:
        verbose_name = "титул"
        verbose_name_plural = "титулы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TitleAward(models.Model):
    """Выдача титула пользователю — только админ/роль с can_grant_titles."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="title_awards", on_delete=models.CASCADE,
    )
    title = models.ForeignKey(
        Title, verbose_name="титул", related_name="awards", on_delete=models.PROTECT,
    )
    reason = models.TextField("за что получен", blank=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто выдал",
        related_name="titles_granted", on_delete=models.PROTECT,
    )
    granted_at = models.DateTimeField("выдан", auto_now_add=True)

    class Meta:
        verbose_name = "выданный титул"
        verbose_name_plural = "выданные титулы"
        ordering = ["-granted_at"]
        unique_together = [("user", "title")]
        permissions = [
            ("can_grant_titles", "Может выдавать титулы пользователям"),
        ]

    def __str__(self):
        return f"{self.user} — {self.title}"
