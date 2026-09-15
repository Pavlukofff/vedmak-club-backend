from django.db import migrations

# Раздел 4.10 плана — реальные разовые активности из документа «Своё Дело».
ACTIVITIES = [
    dict(name="Фехтовальная тренировка", price_real="25.00"),
    dict(name="Стрельба из лука", price_real="28.00"),
    dict(name="Метание ножей", price_real="15.00"),
    dict(name="Файер-тренировка", price_real="20.00"),
]

FENCING = "Фехтовальная тренировка"
ARCHERY = "Стрельба из лука"
KNIVES = "Метание ножей"

# Реальные абонементы-билеты из документа. duration_days — приближение по
# сроку из документа (1 месяц = 30 дней, 6 месяцев = 180, 12 месяцев = 365),
# точных сроков в днях документ не даёт.
SUBSCRIPTIONS = [
    dict(
        name="Билет бойца (выходного дня)",
        description="Анлим на фехтовальные тренировки, только выходные",
        activities=[FENCING],
        perks="Только по выходным дням",
        price_real="130.00", duration_days=30,
    ),
    dict(
        name="Билет бойца (полный месяц)",
        description="Анлим на фехтовальные тренировки",
        activities=[FENCING],
        perks="",
        price_real="150.00", duration_days=30,
    ),
    dict(
        name="Билет стрелка (выходного дня)",
        description="Анлим на стрельбу из лука/арбалета, только выходные",
        activities=[ARCHERY],
        perks="Только по выходным дням",
        price_real="130.00", duration_days=30,
    ),
    dict(
        name="Билет стрелка (полный месяц)",
        description="Анлим на стрельбу из лука/арбалета",
        activities=[ARCHERY],
        perks="",
        price_real="170.00", duration_days=30,
    ),
    dict(
        name="Билет убийцы (полный месяц)",
        description="Анлим на фехтование + стрельба",
        activities=[FENCING, ARCHERY],
        perks="",
        price_real="250.00", duration_days=30,
    ),
    dict(
        name="Билет Ведьмака (полный месяц)",
        description="Анлим на фехтование + стрельба + метание ножей",
        activities=[FENCING, ARCHERY, KNIVES],
        perks="",
        price_real="290.00", duration_days=30,
    ),
    dict(
        name="Билет Стража (полный месяц)",
        description="Анлим на фехтование",
        activities=[FENCING],
        perks=(
            "Приоритетная запись за сутки; бронь 2 тренировок в неделю; "
            "гарантия попадания на 2 тренировки"
        ),
        price_real="190.00", duration_days=30,
    ),
    dict(
        name="Билет Ветерана",
        description="Фехтование + стрельба + метание ножей",
        activities=[FENCING, ARCHERY, KNIVES],
        perks="Всё как у Стража + 1 бесплатный гость в месяц",
        price_real="740.00", duration_days=180,
    ),
    dict(
        name="Билет Командира",
        description="Фехтование + стрельба + метание ножей, годовой",
        activities=[FENCING, ARCHERY, KNIVES],
        perks="Всё как у Ветерана + подарок: личный клинок выбранной школы",
        price_real="1490.00", duration_days=365,
    ),
]


def seed(apps, schema_editor):
    ActivityPrice = apps.get_model("subscriptions", "ActivityPrice")
    Subscription = apps.get_model("subscriptions", "Subscription")

    activities_by_name = {}
    for data in ACTIVITIES:
        obj, _ = ActivityPrice.objects.update_or_create(
            name=data["name"], defaults={"price_real": data["price_real"]},
        )
        activities_by_name[data["name"]] = obj

    for data in SUBSCRIPTIONS:
        sub, _ = Subscription.objects.update_or_create(
            name=data["name"],
            defaults=dict(
                description=data["description"],
                perks=data["perks"],
                price_real=data["price_real"],
                duration_days=data["duration_days"],
            ),
        )
        sub.included_activities.set(
            [activities_by_name[name] for name in data["activities"]],
        )


def unseed(apps, schema_editor):
    ActivityPrice = apps.get_model("subscriptions", "ActivityPrice")
    Subscription = apps.get_model("subscriptions", "Subscription")
    Subscription.objects.filter(name__in=[s["name"] for s in SUBSCRIPTIONS]).delete()
    ActivityPrice.objects.filter(name__in=[a["name"] for a in ACTIVITIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]