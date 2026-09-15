from django.conf import settings
from django.db import models
from django.db.models import F


class EffectType(models.Model):
    """Справочник типов эффектов — раздел 4.8 плана.

    «Ключевой момент: тип эффекта — это справочник, редактируемый в
    админке, а не жёстко зашитый список». Примеры из документа: hp,
    damage, sign_slot, sign_power, poison_resist, aksiy_resist, regen,
    task_add, task_repeat, task_summon, task_refresh, task_retry —
    заведены сид-данными, список свободно пополняется в админке.
    """

    code = models.CharField(
        "код", max_length=50, unique=True,
        help_text="Машиночитаемый код, например 'hp', 'damage', 'sign_slot'",
    )
    name = models.CharField("название", max_length=150)
    description = models.TextField("описание", blank=True)

    class Meta:
        verbose_name = "тип эффекта"
        verbose_name_plural = "типы эффектов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShopItem(models.Model):
    """Товар магазина (включая Лавку алхимика) — раздел 4.8 плана.

    Сайт не рассчитывает бои — эликсир/свиток здесь только карточка
    товара со справочным описанием эффекта для живой отыгровки.
    """

    class Category(models.TextChoices):
        GENERAL = "general", "Обычный товар"
        POTION = "potion", "Зелье/эликсир"
        SCROLL = "scroll", "Свиток"

    name = models.CharField("название", max_length=150)
    category = models.CharField(
        "категория", max_length=20, choices=Category.choices, default=Category.GENERAL,
    )
    price = models.PositiveIntegerField(
        "цена, кроны", blank=True, null=True,
        help_text=(
            "Пусто — для эликсиров: по документу они не покупаются за "
            "фиксированную цену, а крафтятся мастером-алхимиком за рецепт, "
            "кроны и трофеи"
        ),
    )
    description = models.TextField("описание", blank=True)
    image = models.ImageField("изображение", upload_to="shop/", blank=True, null=True)
    stock = models.PositiveIntegerField(
        "остаток", blank=True, null=True, help_text="Ограничение количества; пусто = без лимита",
    )
    is_active = models.BooleanField("активен", default=True)

    min_rank = models.ForeignKey(
        "ranks.Rank", verbose_name="минимальный ранг",
        related_name="+", blank=True, null=True, on_delete=models.PROTECT,
        help_text="Минимальный ранг для использования; обязателен для эликсиров",
    )
    toxicity = models.CharField(
        "токсичность", max_length=100, blank=True,
        help_text=(
            "% токсичности разового применения (только для эликсиров). "
            "Текстовое поле — у части эликсиров ступенчатая токсичность "
            "(«0% за первую, 30% за каждую следующую»)"
        ),
    )

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class ItemEffect(models.Model):
    """Эффект товара — раздел 4.8 плана."""

    class Duration(models.TextChoices):
        INSTANT = "instant", "Мгновенный"
        TEMPORARY = "temporary", "Временный"
        PERMANENT = "permanent", "Постоянный"

    item = models.ForeignKey(
        ShopItem, verbose_name="товар", related_name="effects", on_delete=models.CASCADE,
    )
    type = models.ForeignKey(
        EffectType, verbose_name="тип эффекта", related_name="item_effects",
        on_delete=models.PROTECT,
    )
    value = models.IntegerField(
        "значение", blank=True, null=True,
        help_text="Числовое значение эффекта, например +2 макс. ХП",
    )
    duration = models.CharField(
        "длительность", max_length=20, choices=Duration.choices, default=Duration.INSTANT,
    )
    duration_value = models.PositiveIntegerField(
        "на сколько", blank=True, null=True,
        help_text="Если временный — на сколько тактов/боёв",
    )

    class Meta:
        verbose_name = "эффект товара"
        verbose_name_plural = "эффекты товара"

    def __str__(self):
        return f"{self.item} — {self.type}"


class Purchase(models.Model):
    """Покупка/выдача товара — «Мои покупки / инвентарь» (раздел 1 плана).

    Этой модели нет в детальных разделах плана (4.x) — там описан только
    каталог. Спроектирована по аналогии с уже реализованными механиками:
    - price_paid проставлен -> это самостоятельная покупка за кроны;
    - price_paid пуст -> ручная выдача (например, скрафченный эликсир от
      мастера-алхимика) ролью с правом can_grant_items, без оплаты.
    Списание баланса и уменьшение stock — в save(), один раз при создании,
    независимо от того, где создана запись (API или админка).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        related_name="purchases", on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        ShopItem, verbose_name="товар", related_name="purchases", on_delete=models.PROTECT,
    )
    price_paid = models.PositiveIntegerField(
        "уплачено, кроны", blank=True, null=True,
        help_text="Пусто — если выдано вручную без оплаты",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто выдал вручную",
        related_name="items_granted", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Пусто, если товар куплен самим пользователем",
    )
    purchased_at = models.DateTimeField("получено", auto_now_add=True)
    is_used = models.BooleanField(
        "использован", default=False,
        help_text="Свиток возвращён мастеру / зелье выпито и т.п.",
    )
    used_at = models.DateTimeField("использован когда", blank=True, null=True)

    class Meta:
        verbose_name = "покупка"
        verbose_name_plural = "покупки"
        ordering = ["-purchased_at"]
        permissions = [
            ("can_grant_items", "Может выдавать товары вручную без оплаты"),
        ]

    def __str__(self):
        return f"{self.user} — {self.item}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            if self.price_paid:
                self.user.balance = F("balance") - self.price_paid
                self.user.save(update_fields=["balance"])
            if self.item.stock is not None:
                self.item.stock = F("stock") - 1
                self.item.save(update_fields=["stock"])