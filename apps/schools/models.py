from django.db import models


class School(models.Model):
    """Справочная карточка школы фехтования — раздел 4.6 плана.

    Параметры школы (оружие, ХП, урон и т.д.) используются только как
    справочная информация для живых РПГ-боёв в клубе — сайт бои не считает.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        IN_DEVELOPMENT = "in_development", "В разработке"

    name = models.CharField("название", max_length=100, unique=True)
    description = models.TextField("описание", blank=True)
    icon = models.ImageField("иконка", upload_to="schools/icons/", blank=True, null=True)
    emblem = models.ImageField("герб", upload_to="schools/emblems/", blank=True, null=True)

    weapon_type = models.CharField(
        "тип оружия", max_length=255,
        help_text="Например, «Полуторный меч»; для школ с несколькими типами оружия — перечисляется текстом",
    )
    base_hp = models.PositiveIntegerField("базовое ХП", blank=True, null=True)
    base_damage = models.CharField(
        "базовый урон", max_length=255, blank=True,
        help_text="Текстовое поле, а не число — например, у Лисы: «лук 2–3 (по дистанции), меч 1»",
    )
    sign_slots = models.PositiveIntegerField("слоты знаков", blank=True, null=True)
    intoxication_threshold = models.PositiveIntegerField(
        "порог интоксикации, %", blank=True, null=True,
    )
    special_abilities = models.TextField("особенности", blank=True)

    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )

    class Meta:
        verbose_name = "школа"
        verbose_name_plural = "школы"
        ordering = ["name"]

    def __str__(self):
        return self.name