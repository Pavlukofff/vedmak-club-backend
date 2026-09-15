from .birthdays import upcoming_birthdays
from .models import ActivityLogEntry


def dashboard_callback(request, context):
    """UNFOLD["DASHBOARD_CALLBACK"] — раздел 4.13 плана: сводная страница

    открывается первой при входе в админку. Добавляет в контекст стартовой
    страницы Django admin последние события ленты и ближайшие дни рождения.
    """
    context["activity_feed"] = ActivityLogEntry.objects.select_related(
        "actor", "target",
    )[:15]
    context["upcoming_birthdays"] = upcoming_birthdays(days=7)
    return context
