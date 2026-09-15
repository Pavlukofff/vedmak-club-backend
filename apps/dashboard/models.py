from django.conf import settings
from django.db import models


class ActivityLogEntry(models.Model):
    """Лента событий для Dashboard админ-панели — раздел 4.13 плана.

    Заполняется автоматически сигналами (см. signals.py) при создании/
    изменении ключевых объектов. Дни рождения сюда не пишутся — это
    отдельная вычисляемая выборка (см. birthdays.py), как и указано в плане.
    """

    class Type(models.TextChoices):
        USER_REGISTERED = "user_registered", "Новая регистрация"
        DISPLAYNAME_REQUEST = "displayname_request", "Запрос на смену никнейма"
        DISPLAYNAME_REVIEWED = "displayname_reviewed", "Заявка на смену никнейма рассмотрена"
        RANK_REQUEST = "rank_request", "Заявка на повышение ранга"
        RANK_REQUEST_REVIEWED = "rank_request_reviewed", "Заявка на ранг рассмотрена"
        RANK_CHANGED = "rank_changed", "Изменение ранга"
        BATTLE_RECORDED = "battle_recorded", "Записан бой"
        MONSTER_KILL_RECORDED = "monster_kill_recorded", "Записано убийство монстра"
        CURRENCY_GRANTED = "currency_granted", "Начислена валюта"
        CURRENCY_TRANSFERRED = "currency_transferred", "Перевод валюты между пользователями"
        PENALTY_ISSUED = "penalty_issued", "Вынесено взыскание"
        PENALTY_CANCELLED = "penalty_cancelled", "Отменено взыскание"
        TITLE_GRANTED = "title_granted", "Выдан титул"
        TITLE_REVOKED = "title_revoked", "Отозван титул"
        BRACKET_GENERATED = "bracket_generated", "Сгенерирована турнирная сетка"
        PURCHASE_GRANTED = "purchase_granted", "Товар выдан вручную"
        FUNDRAISER_CONTRIBUTION = "fundraiser_contribution", "Зафиксирован взнос в сбор средств"

    type = models.CharField("тип", max_length=30, choices=Type.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто совершил",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кого касается",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )
    related_object_id = models.CharField("id связанного объекта", max_length=50, blank=True)
    message = models.TextField("сообщение")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "событие ленты"
        verbose_name_plural = "лента событий"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
