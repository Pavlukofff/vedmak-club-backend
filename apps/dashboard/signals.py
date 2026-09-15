from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from apps.accounts.models import CurrencyTransfer, DisplayNameChangeRequest, User
from apps.battles.models import Battle
from apps.bestiary.models import MonsterKill
from apps.fundraisers.models import FundraiserContribution
from apps.penalties.models import Penalty
from apps.ranks.models import RankUpRequest
from apps.shop.models import Purchase
from apps.titles.models import TitleAward

from .models import ActivityLogEntry


@receiver(post_save, sender=User)
def log_user_registered(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.USER_REGISTERED,
            target=instance,
            message=f"Новая регистрация: {instance.display_name} ({instance.username})",
        )


@receiver(pre_save, sender=User)
def _cache_previous_user_state(sender, instance, **kwargs):
    """Снимок rank_id/balance до записи — для диффа в log_user_changes ниже."""
    if not instance.pk:
        instance._previous_state = None
        return
    instance._previous_state = User.objects.filter(pk=instance.pk).values(
        "rank_id", "balance",
    ).first()


@receiver(post_save, sender=User)
def log_user_rank_and_balance_changes(sender, instance, created, **kwargs):
    """actor берётся из instance._activity_actor — транзитного атрибута,

    который проставляет вызывающий код (view/admin), где известно, кто
    именно совершил действие (утвердил ранг, выдал награду и т.д.).
    """
    if created or getattr(instance, "_is_registration_default_save", False):
        return

    previous = getattr(instance, "_previous_state", None)
    if not previous:
        return
    actor = getattr(instance, "_activity_actor", None)

    if previous["rank_id"] != instance.rank_id:
        rank_name = instance.rank.name if instance.rank_id else "без ранга"
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.RANK_CHANGED,
            actor=actor,
            target=instance,
            related_object_id=str(instance.rank_id or ""),
            message=(
                f"{actor.display_name if actor else '—'}: изменил(а) ранг "
                f"{instance.display_name} на «{rank_name}»"
            ),
        )

    if (
        instance.balance > previous["balance"]
        and not getattr(instance, "_skip_currency_log", False)
    ):
        delta = instance.balance - previous["balance"]
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.CURRENCY_GRANTED,
            actor=actor,
            target=instance,
            message=(
                f"{actor.display_name if actor else '—'}: начислил(а) {delta} крон "
                f"пользователю {instance.display_name} (баланс {instance.balance})"
            ),
        )


@receiver(post_save, sender=CurrencyTransfer)
def log_currency_transfer(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.CURRENCY_TRANSFERRED,
            actor=instance.sender,
            target=instance.recipient,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.sender.display_name} перевёл(а) {instance.amount} крон "
                f"пользователю {instance.recipient.display_name}"
            ),
        )


@receiver(post_save, sender=DisplayNameChangeRequest)
def log_displayname_request(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.DISPLAYNAME_REQUEST,
            actor=instance.user,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=f"{instance.user.display_name} просит сменить имя на «{instance.requested_name}»",
        )


@receiver(pre_save, sender=DisplayNameChangeRequest)
def _cache_previous_displayname_status(sender, instance, **kwargs):
    instance._previous_status = (
        DisplayNameChangeRequest.objects.filter(pk=instance.pk).values_list(
            "status", flat=True,
        ).first()
        if instance.pk else None
    )


@receiver(post_save, sender=DisplayNameChangeRequest)
def log_displayname_reviewed(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, "_previous_status", None)
    if previous == DisplayNameChangeRequest.Status.PENDING and instance.status != previous:
        verdict = "одобрил(а)" if instance.status == DisplayNameChangeRequest.Status.APPROVED else "отклонил(а)"
        reviewer = instance.reviewed_by
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.DISPLAYNAME_REVIEWED,
            actor=reviewer,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{reviewer.display_name if reviewer else '—'} {verdict} смену ника "
                f"{instance.user.display_name} на «{instance.requested_name}»"
            ),
        )


@receiver(post_save, sender=RankUpRequest)
def log_rank_request(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.RANK_REQUEST,
            actor=instance.user,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=f"{instance.user.display_name} подал(а) заявку на ранг «{instance.to_rank.name}»",
        )


@receiver(pre_save, sender=RankUpRequest)
def _cache_previous_rank_request_status(sender, instance, **kwargs):
    instance._previous_status = (
        RankUpRequest.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        if instance.pk else None
    )


@receiver(post_save, sender=RankUpRequest)
def log_rank_request_reviewed(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, "_previous_status", None)
    if previous == RankUpRequest.Status.PENDING and instance.status != previous:
        verdict = "одобрил(а)" if instance.status == RankUpRequest.Status.APPROVED else "отклонил(а)"
        reviewer = instance.reviewed_by
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.RANK_REQUEST_REVIEWED,
            actor=reviewer,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{reviewer.display_name if reviewer else '—'} {verdict} заявку "
                f"{instance.user.display_name} на ранг «{instance.to_rank.name}»"
            ),
        )


@receiver(post_save, sender=Battle)
def log_battle_recorded(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.BATTLE_RECORDED,
            actor=instance.recorded_by,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.recorded_by.display_name}: зафиксирован бой "
                f"{instance.fighter1.display_name} vs {instance.fighter2.display_name}"
            ),
        )


@receiver(post_save, sender=MonsterKill)
def log_monster_kill_recorded(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.MONSTER_KILL_RECORDED,
            actor=instance.recorded_by,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=f"{instance.recorded_by.display_name}: записал(а) убийство «{instance.bestiary.name}» ({instance.user.display_name})",
        )


@receiver(post_save, sender=Penalty)
def log_penalty_issued(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.PENALTY_ISSUED,
            actor=instance.issued_by,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.issued_by.display_name}: вынес(ла) взыскание "
                f"«{instance.get_type_display()}» для {instance.user.display_name}"
            ),
        )


@receiver(pre_save, sender=Penalty)
def _cache_previous_penalty_status(sender, instance, **kwargs):
    instance._previous_status = (
        Penalty.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        if instance.pk else None
    )


@receiver(post_save, sender=Penalty)
def log_penalty_cancelled(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, "_previous_status", None)
    if previous and previous != Penalty.Status.CANCELLED and instance.status == Penalty.Status.CANCELLED:
        canceller = instance.cancelled_by
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.PENALTY_CANCELLED,
            actor=canceller,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{canceller.display_name if canceller else '—'}: отменил(а) взыскание "
                f"«{instance.get_type_display()}» для {instance.user.display_name}"
            ),
        )


@receiver(post_save, sender=TitleAward)
def log_title_granted(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.TITLE_GRANTED,
            actor=instance.granted_by,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.granted_by.display_name}: выдал(а) титул «{instance.title.name}» "
                f"пользователю {instance.user.display_name}"
            ),
        )


@receiver(pre_delete, sender=TitleAward)
def log_title_revoked(sender, instance, **kwargs):
    actor = getattr(instance, "_deleted_by", None)
    ActivityLogEntry.objects.create(
        type=ActivityLogEntry.Type.TITLE_REVOKED,
        actor=actor,
        target=instance.user,
        related_object_id=str(instance.pk),
        message=(
            f"{actor.display_name if actor else '—'}: отозвал(а) титул «{instance.title.name}» "
            f"у {instance.user.display_name}"
        ),
    )


@receiver(post_save, sender=Purchase)
def log_purchase_granted(sender, instance, created, **kwargs):
    if created and instance.granted_by_id:
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.PURCHASE_GRANTED,
            actor=instance.granted_by,
            target=instance.user,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.granted_by.display_name}: выдал(а) «{instance.item.name}» "
                f"пользователю {instance.user.display_name}"
            ),
        )


@receiver(post_save, sender=FundraiserContribution)
def log_fundraiser_contribution(sender, instance, created, **kwargs):
    if created:
        donor = instance.contributor.display_name if instance.contributor_id else (
            instance.contributor_name or "аноним"
        )
        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.FUNDRAISER_CONTRIBUTION,
            actor=instance.recorded_by,
            target=instance.contributor,
            related_object_id=str(instance.pk),
            message=(
                f"{instance.recorded_by.display_name}: зафиксировал(а) взнос {instance.amount} BYN "
                f"от {donor} в сбор «{instance.fundraiser.title}»"
            ),
        )
