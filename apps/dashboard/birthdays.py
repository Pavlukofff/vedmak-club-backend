from datetime import date

from django.utils import timezone

from apps.accounts.models import User


def upcoming_birthdays(days=7):
    """Раздел 4.13 плана: «вычисляемый список, у кого ДР в ближайшие N дней»,

    не через ActivityLogEntry. Инструмент для админки — показывает дату
    рождения независимо от birth_date_visibility пользователя.
    """
    today = timezone.localdate()
    users = User.objects.filter(birth_date__isnull=False, is_active=True)

    upcoming = []
    for user in users:
        birth_date = user.birth_date
        try:
            next_birthday = birth_date.replace(year=today.year)
        except ValueError:
            # 29 февраля в невисокосный год
            next_birthday = date(today.year, 2, 28)
        if next_birthday < today:
            try:
                next_birthday = birth_date.replace(year=today.year + 1)
            except ValueError:
                next_birthday = date(today.year + 1, 2, 28)

        days_until = (next_birthday - today).days
        if 0 <= days_until <= days:
            upcoming.append({
                "user": user,
                "next_birthday": next_birthday,
                "days_until": days_until,
            })

    upcoming.sort(key=lambda row: row["days_until"])
    return upcoming
