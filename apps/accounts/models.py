from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F

from apps.ranks.models import Rank
from apps.schools.models import School


class User(AbstractUser):
    """Пользователь клуба — раздел 4.3 плана.

    Роли и права пользователя не хранятся отдельным полем — используются
    встроенные django.contrib.auth Group/Permission (см. раздел 2 плана:
    «роль + набор прав», что Group/Permission уже реализуют из коробки).

    username, first_name, last_name, is_active, date_joined наследуются
    от AbstractUser и покрывают поля «Логин», «Имя», «Фамилия» (опционально),
    isActive и createdAt из плана.
    """

    class NameVisibility(models.TextChoices):
        HIDDEN = "hidden", "Скрыто"
        PUBLIC = "public", "Публично"

    class BirthDateVisibility(models.TextChoices):
        HIDDEN = "hidden", "Скрыто"
        DAY_MONTH = "day_month", "Только день и месяц"
        FULL = "full", "Полностью"

    email = models.EmailField("email", unique=True)
    email_verified = models.BooleanField("email подтверждён", default=False)

    display_name = models.CharField(
        "отображаемое имя", max_length=100, unique=True,
        help_text="Никнейм персонажа, свободный выбор при регистрации; далее меняется только через запрос",
    )
    name_visibility = models.CharField(
        "видимость имени и фамилии", max_length=10,
        choices=NameVisibility.choices, default=NameVisibility.HIDDEN,
    )

    avatar = models.ImageField("аватар", upload_to="avatars/", blank=True, null=True)

    school = models.ForeignKey(
        School, verbose_name="школа", related_name="members",
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Изначально не назначена; назначается админом/мастером",
    )
    rank = models.ForeignKey(
        Rank, verbose_name="ранг цеха", related_name="members",
        blank=True, null=True, on_delete=models.PROTECT,
        help_text="Изначально «Рекрут» — присваивается автоматически при регистрации",
    )

    level = models.PositiveIntegerField("уровень", default=1)
    experience = models.PositiveIntegerField("опыт", default=0)
    balance = models.PositiveIntegerField(
        "баланс, кроны", default=0,
        help_text="Внутриигровая валюта, начисляется только вручную через админку",
    )

    birth_date = models.DateField("дата рождения", blank=True, null=True)
    birth_date_visibility = models.CharField(
        "видимость даты рождения", max_length=10,
        choices=BirthDateVisibility.choices, default=BirthDateVisibility.HIDDEN,
    )

    character_description = models.TextField(
        "описание персонажа", blank=True,
        help_text="Необязательная ролевая справка о персонаже — предыстория, характер и т.д.",
    )

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def save(self, *args, **kwargs):
        # createsuperuser и другие пути создания пользователя не всегда
        # передают display_name (не входит в REQUIRED_FIELDS) — без
        # фолбэка это столкнётся с unique=True при второй такой записи.
        if not self.display_name:
            self.display_name = self.username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.username


class DisplayNameChangeRequest(models.Model):
    """Запрос пользователя на смену отображаемого имени — раздел 4.5 плана.

    После регистрации displayName меняется не напрямую, а через очередь
    заявок на рассмотрение в админ-панели.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрено"
        REJECTED = "rejected", "Отклонено"

    user = models.ForeignKey(
        User, verbose_name="пользователь",
        related_name="displayname_change_requests", on_delete=models.CASCADE,
    )
    current_name = models.CharField("текущее имя", max_length=100)
    requested_name = models.CharField("желаемое имя", max_length=100)
    reason = models.TextField("причина", blank=True)
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        User, verbose_name="кто рассмотрел", related_name="+",
        blank=True, null=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField("создана", auto_now_add=True)
    reviewed_at = models.DateTimeField("рассмотрена", blank=True, null=True)

    class Meta:
        verbose_name = "запрос на смену имени"
        verbose_name_plural = "запросы на смену имени"
        ordering = ["-created_at"]
        permissions = [
            ("can_review_displayname_requests", "Может рассматривать заявки на смену никнейма"),
        ]

    def __str__(self):
        return f"{self.user}: {self.current_name} → {self.requested_name} ({self.get_status_display()})"


class AvatarPreset(models.Model):
    """Пресет-аватар из галереи — раздел 4.2 плана.

    Доступны сразу после регистрации без каких-либо условий (в отличие от
    загрузки своего изображения, которая требует подтверждённого email).
    """

    title = models.CharField("название", max_length=100, blank=True)
    category = models.CharField(
        "категория", max_length=50, blank=True,
        help_text="Например: школы ведьмаков, монстры, персонажи",
    )
    image = models.ImageField("изображение", upload_to="avatar_presets/")
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "пресет аватара"
        verbose_name_plural = "пресеты аватаров"
        ordering = ["category", "title"]

    def __str__(self):
        return self.title or f"Пресет #{self.pk}"


class SiteSettings(models.Model):
    """Общие настройки сайта, редактируемые админом — синглтон-модель.

    Раздел 4.1 плана: «баланс = стартовое количество монет (настраивается
    админом)».
    """

    starting_balance = models.PositiveIntegerField(
        "стартовый баланс новых пользователей, кроны", default=0,
    )

    class Meta:
        verbose_name = "настройки сайта"
        verbose_name_plural = "настройки сайта"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Настройки сайта"


class CurrencyTransfer(models.Model):
    """Передача кронов между пользователями — самообслуживание, любому

    пользователю. Списание/начисление — в save(), один раз при создании,
    тем же паттерном, что и остальные денежные операции в проекте.
    """

    sender = models.ForeignKey(
        User, verbose_name="отправитель", related_name="currency_transfers_sent",
        on_delete=models.PROTECT,
    )
    recipient = models.ForeignKey(
        User, verbose_name="получатель", related_name="currency_transfers_received",
        on_delete=models.PROTECT,
    )
    amount = models.PositiveIntegerField("сумма, кроны")
    message = models.CharField("сообщение", max_length=200, blank=True)
    created_at = models.DateTimeField("отправлено", auto_now_add=True)

    class Meta:
        verbose_name = "перевод валюты"
        verbose_name_plural = "переводы валюты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.amount}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # instance.save() (не queryset.update()), чтобы сработали сигналы
            # дашборда. _skip_currency_log — у перевода уже есть свой,
            # более информативный тип события (currency_transferred),
            # дублировать его общим "начислена валюта" не нужно.
            self.sender.balance = F("balance") - self.amount
            self.sender.save(update_fields=["balance"])
            self.recipient.balance = F("balance") + self.amount
            self.recipient._skip_currency_log = True
            self.recipient.save(update_fields=["balance"])