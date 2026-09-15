from django.conf import settings
from django.db import models


class Rank(models.Model):
    """Ранг цеха — раздел 4.11 плана.

    Иерархия: Рекрут -> Ученик -> Бронзовый кандидат -> Серебряный кандидат ->
    Золотой кандидат -> Младший ведьмак -> Признанный Ведьмак -> Мастер Ведьмак.
    """

    name = models.CharField("название", max_length=100, unique=True)
    icon = models.CharField(
        "иконка/эмодзи", max_length=16, blank=True,
        help_text="Например, 🛡 или ⚔️",
    )
    order = models.PositiveIntegerField(
        "порядок", unique=True,
        help_text="Порядок в иерархии — используется для сортировки и проверки условий вида «и выше»",
    )

    class Meta:
        verbose_name = "ранг"
        verbose_name_plural = "ранги"
        ordering = ["order"]

    def __str__(self):
        return self.name


class RankRequirement(models.Model):
    """Одно из требований для получения ранга — расширяемый список условий."""

    class Type(models.TextChoices):
        LEVEL = "level", "Уровень"
        WINS_VS_RANK = "wins_vs_rank", "Победы над рангом"
        RPG_WINS = "rpg_wins", "РПГ-победы"
        JOURNEYMAN_COUNT = "journeyman_count", "Кол-во подмастерьев"
        MASTER_COUNT = "master_count", "Кол-во мастеров"
        TRIAL = "trial", "Испытание"
        MONSTER_TROPHIES = "monster_trophies", "Трофеи с монстров"
        QUEST_LINES = "quest_lines", "Квестовые линии"
        CUSTOM = "custom", "Другое"

    rank = models.ForeignKey(
        Rank, verbose_name="ранг", related_name="requirements", on_delete=models.CASCADE,
    )
    type = models.CharField("тип условия", max_length=30, choices=Type.choices)
    value = models.PositiveIntegerField("значение", blank=True, null=True)
    target_rank = models.ForeignKey(
        Rank, verbose_name="целевой ранг", related_name="+",
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Для условий вида «N побед над членами ранга X и выше»",
    )
    description = models.CharField(
        "описание", max_length=255, blank=True,
        help_text="Для нестандартных условий вроде «испытание травами»",
    )

    class Meta:
        verbose_name = "требование ранга"
        verbose_name_plural = "требования ранга"

    def __str__(self):
        return f"{self.rank} — {self.get_type_display()}"


class RankReward(models.Model):
    """Одна из наград за получение ранга — расширяемый список наград."""

    class Type(models.TextChoices):
        ITEM = "item", "Предмет"
        DISCOUNT = "discount", "Скидка"
        BOARD_PLACEMENT = "board_placement", "Место на доске почёта"
        TITLE = "title", "Титул"
        SLOT = "slot", "Слот"
        CUSTOM = "custom", "Другое"

    rank = models.ForeignKey(
        Rank, verbose_name="ранг", related_name="rewards", on_delete=models.CASCADE,
    )
    type = models.CharField("тип награды", max_length=30, choices=Type.choices)
    value = models.CharField("значение", max_length=255, blank=True)
    description = models.CharField("описание", max_length=255, blank=True)

    class Meta:
        verbose_name = "награда ранга"
        verbose_name_plural = "награды ранга"

    def __str__(self):
        return f"{self.rank} — {self.get_type_display()}"


class RankUpRequest(models.Model):
    """Заявка пользователя на повышение ранга — раздел 4.11 плана.

    Присваивается только вручную, по заявке с ручной проверкой мастером/админом.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрено"
        REJECTED = "rejected", "Отклонено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="rank_up_requests", on_delete=models.CASCADE,
    )
    from_rank = models.ForeignKey(
        Rank, verbose_name="текущий ранг", related_name="+", on_delete=models.PROTECT,
    )
    to_rank = models.ForeignKey(
        Rank, verbose_name="желаемый ранг", related_name="+", on_delete=models.PROTECT,
    )
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто рассмотрел", related_name="+",
        blank=True, null=True, on_delete=models.SET_NULL,
    )
    comment = models.TextField("комментарий", blank=True)
    created_at = models.DateTimeField("создана", auto_now_add=True)
    reviewed_at = models.DateTimeField("рассмотрена", blank=True, null=True)

    class Meta:
        verbose_name = "заявка на повышение ранга"
        verbose_name_plural = "заявки на повышение ранга"
        ordering = ["-created_at"]
        permissions = [
            ("can_approve_ranks", "Может подтверждать заявки на повышение ранга"),
        ]

    def __str__(self):
        return f"{self.user} → {self.to_rank} ({self.get_status_display()})"