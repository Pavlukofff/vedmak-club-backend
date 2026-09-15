from django.db.models import Q

from .models import Battle


def battle_stats_for_user(user):
    """Побед/поражений/винрейт одного пользователя — раздел 4.4 плана."""
    total = Battle.objects.filter(Q(fighter1=user) | Q(fighter2=user)).count()
    wins = Battle.objects.filter(winner=user).count()
    losses = (
        Battle.objects.filter(Q(fighter1=user) | Q(fighter2=user), winner__isnull=False)
        .exclude(winner=user)
        .count()
    )
    draws = total - wins - losses
    winrate = round(wins / total * 100, 1) if total else 0.0
    return {"battles": total, "wins": wins, "losses": losses, "draws": draws, "winrate": winrate}


def battle_ratings():
    """Рейтинг побед/поражений по всем участникам — раздел 1 плана.

    Однопроходная агрегация по всем боям (без N+1 по пользователям).
    """
    buckets = {}

    def bucket(user_id):
        return buckets.setdefault(
            user_id, {"battles": 0, "wins": 0, "losses": 0, "draws": 0},
        )

    rows = Battle.objects.values_list("fighter1_id", "fighter2_id", "winner_id")
    for fighter1_id, fighter2_id, winner_id in rows:
        for fighter_id in (fighter1_id, fighter2_id):
            b = bucket(fighter_id)
            b["battles"] += 1
            if winner_id is None:
                b["draws"] += 1
            elif winner_id == fighter_id:
                b["wins"] += 1
            else:
                b["losses"] += 1

    from apps.accounts.models import User

    users = User.objects.in_bulk(buckets.keys())
    ratings = []
    for user_id, stats in buckets.items():
        user = users.get(user_id)
        if user is None:
            continue
        winrate = round(stats["wins"] / stats["battles"] * 100, 1) if stats["battles"] else 0.0
        ratings.append({
            "username": user.username,
            "display_name": user.display_name,
            **stats,
            "winrate": winrate,
        })

    ratings.sort(key=lambda r: (-r["wins"], -r["winrate"]))
    return ratings
