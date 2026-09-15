from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.ranks.models import Rank

from .models import AvatarPreset, SiteSettings, User


@receiver(post_save, sender=User)
def assign_defaults_on_create(sender, instance, created, **kwargs):
    """Раздел 4.1 плана: стартовые значения нового пользователя.

    Ранг «Рекрут», стартовый баланс (настраивается админом через
    SiteSettings) и дефолтный пресет-аватар назначаются автоматически.
    Повторный instance.save() ниже не зацикливается: он проходит как
    created=False, и обработчик сразу возвращается.
    """
    if not created:
        return

    update_fields = []

    if instance.rank_id is None:
        recruit_rank = Rank.objects.order_by("order").first()
        if recruit_rank is not None:
            instance.rank = recruit_rank
            update_fields.append("rank")

    if instance.balance == 0:
        starting_balance = SiteSettings.load().starting_balance
        if starting_balance:
            instance.balance = starting_balance
            update_fields.append("balance")

    if not instance.avatar:
        preset = AvatarPreset.objects.filter(is_active=True).order_by("?").first()
        if preset is not None:
            instance.avatar.save(
                preset.image.name.rsplit("/", 1)[-1],
                ContentFile(preset.image.read()),
                save=False,
            )
            update_fields.append("avatar")

    if update_fields:
        # Метка для apps.dashboard.signals: это назначение стартовых
        # значений при регистрации, не «изменение ранга»/«начисление
        # валюты» в смысле ленты событий дашборда (раздел 4.13 плана) —
        # такое событие и так покрыто записью user_registered.
        instance._is_registration_default_save = True
        instance.save(update_fields=update_fields)
