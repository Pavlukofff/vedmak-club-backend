from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.battles.models import Battle


@receiver(post_save, sender=Battle)
def sync_tournament_match_on_battle_save(sender, instance, **kwargs):
    """Если бой привязан к ячейке турнирной сетки — пересчитать победителя

    ячейки и продвинуть его дальше (TournamentMatch.save() делает это сам).
    """
    match = getattr(instance, "tournament_match", None)
    if match is not None:
        match.save()
