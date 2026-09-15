from django.conf import settings
from django.db import models
from django.utils import timezone


class Battle(models.Model):
    """Бой — раздел 4.14 плана («Дуэльный кодекс и модель боя»).

    Сайт не проводит и не рассчитывает бои — это запись результата живой
    фехтовальной схватки, зафиксированная судьёй/админом постфактум.
    """

    class Type(models.TextChoices):
        TRAINING = "ТС", "Тренировочная Схватка (на очки)"
        ROLEPLAY = "РС", "Ролевая Схватка (до поражения аватара)"

    type = models.CharField("тип боя", max_length=2, choices=Type.choices)

    fighter1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="участник 1",
        related_name="battles_as_fighter1", on_delete=models.PROTECT,
    )
    fighter2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="участник 2",
        related_name="battles_as_fighter2", on_delete=models.PROTECT,
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="победитель",
        related_name="battles_won", blank=True, null=True, on_delete=models.PROTECT,
        help_text="Может отсутствовать — ничья/дубль",
    )

    main_judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="главный судья",
        related_name="battles_as_main_judge", blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text="Обязателен для ранговых/квестовых боёв; в тренировочных — по усмотрению мастеров",
    )
    side_judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="боковой судья",
        related_name="battles_as_side_judge", blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    is_ranked = models.BooleanField(
        "ранговый/квестовый", default=False,
        help_text="Иначе — тренировочный бой",
    )
    tournament = models.ForeignKey(
        "tournaments.Tournament", verbose_name="турнир",
        related_name="battles", blank=True, null=True, on_delete=models.SET_NULL,
    )
    date = models.DateTimeField("дата и время", default=timezone.now)
    notes = models.TextField("заметки", blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто зафиксировал",
        related_name="battles_recorded", on_delete=models.PROTECT,
        help_text="Запись создаёт только судья/админ — без самозаявления участников",
    )

    class Meta:
        verbose_name = "бой"
        verbose_name_plural = "бои"
        ordering = ["-date"]
        permissions = [
            ("can_record_battles", "Может фиксировать результаты боёв"),
        ]

    def __str__(self):
        return f"{self.fighter1} vs {self.fighter2} ({self.get_type_display()})"