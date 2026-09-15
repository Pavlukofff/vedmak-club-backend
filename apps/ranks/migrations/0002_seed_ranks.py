from django.db import migrations

# Порядок и данные — раздел 4.11 плана, таблица рангов цеха.
RANKS = [
    dict(order=1, name="Рекрут цеха", icon="🛡"),
    dict(order=2, name="Ученик цеха", icon="⚔️"),
    dict(order=3, name="Бронзовый кандидат цеха", icon="🏅"),
    dict(order=4, name="Серебряный кандидат цеха", icon="🏅"),
    dict(order=5, name="Золотой кандидат цеха", icon="🏅"),
    dict(order=6, name="Младший ведьмак школы", icon="🐺"),
    dict(order=7, name="Признанный Ведьмак", icon="🐺"),
    dict(order=8, name="Мастер Ведьмак", icon="🏆"),
]

# requirements/rewards ключуются по order ранга.
REQUIREMENTS = {
    1: [
        dict(type="level", value=0, description="Присваивается автоматически при регистрации"),
    ],
    2: [
        dict(type="level", value=5),
        dict(type="wins_vs_rank", value=3, target_rank_order=2),
    ],
    3: [
        dict(type="level", value=15),
        dict(type="wins_vs_rank", value=5, target_rank_order=3),
    ],
    4: [
        dict(type="level", value=25),
        dict(type="wins_vs_rank", value=10, target_rank_order=3),
        dict(type="rpg_wins", value=3),
        dict(type="journeyman_count", value=3),
        dict(type="master_count", value=2),
        dict(type="trial", description="Испытание травами"),
        dict(type="trial", description="Поиск святилищ"),
        dict(type="monster_trophies", value=3),
    ],
    5: [
        dict(type="level", value=35),
        dict(type="wins_vs_rank", value=15, target_rank_order=3),
        dict(type="rpg_wins", value=6),
        dict(type="journeyman_count", value=6),
        dict(type="master_count", value=3),
        dict(type="monster_trophies", value=9),
    ],
    6: [
        dict(type="level", value=50),
        dict(type="trial", description="Испытание медальоном"),
    ],
    7: [
        dict(type="level", value=70),
        dict(type="wins_vs_rank", value=21),
        dict(type="rpg_wins", value=11),
        dict(type="custom", description="Все подмастерья"),
        dict(type="custom", description="Все мастера"),
        dict(type="quest_lines", value=6),
        dict(type="custom", description="1 отвар"),
        dict(type="custom", description="1 ветка мутаций"),
    ],
    8: [
        dict(
            type="custom",
            description=(
                "Уточняется — требования публикуются в телеграм-канале "
                "клуба и могут меняться"
            ),
        ),
    ],
}

REWARDS = {
    1: [
        dict(type="item", value="Кулон рекрута цеха"),
    ],
    2: [
        dict(type="custom", description="Допуск к выполнению более сложных линеек цеха"),
        dict(type="board_placement", value="Доска почёта"),
    ],
    3: [
        dict(type="item", value="Браслет бронзового кандидата"),
        dict(type="board_placement", value="Доска почёта бронзовых кандидатов"),
    ],
    4: [
        dict(type="item", value="Браслет серебряного кандидата"),
        dict(type="discount", value="10%"),
        dict(type="board_placement", value="Доска почёта серебряных кандидатов"),
    ],
    5: [
        dict(type="item", value="Браслет золотого кандидата"),
        dict(type="discount", value="20%"),
        dict(type="board_placement", value="Доска почёта золотых кандидатов"),
    ],
    6: [
        dict(type="item", value="Медальон школы"),
        dict(type="item", value="Знаки школы"),
        dict(type="discount", value="30%"),
        dict(type="board_placement", value="Доска почёта младших ведьмаков"),
    ],
    7: [
        dict(type="item", value="Личный клинок"),
        dict(type="slot", value="Слоты брони персонажа"),
        dict(type="custom", value="Личный алхимик"),
        dict(type="discount", value="50%"),
        dict(type="discount", value="50% на крафт"),
        dict(type="board_placement", value="Доска почёта"),
    ],
    8: [
        dict(type="custom", description="Уточняется"),
    ],
}


def seed_ranks(apps, schema_editor):
    Rank = apps.get_model("ranks", "Rank")
    RankRequirement = apps.get_model("ranks", "RankRequirement")
    RankReward = apps.get_model("ranks", "RankReward")

    ranks_by_order = {}
    for data in RANKS:
        rank, _ = Rank.objects.update_or_create(order=data["order"], defaults=data)
        ranks_by_order[data["order"]] = rank

    for order, rank in ranks_by_order.items():
        rank.requirements.all().delete()
        for req in REQUIREMENTS.get(order, []):
            req = dict(req)
            target_order = req.pop("target_rank_order", None)
            RankRequirement.objects.create(
                rank=rank,
                target_rank=ranks_by_order.get(target_order) if target_order else None,
                **req,
            )

        rank.rewards.all().delete()
        for rew in REWARDS.get(order, []):
            RankReward.objects.create(rank=rank, **rew)


def remove_ranks(apps, schema_editor):
    Rank = apps.get_model("ranks", "Rank")
    Rank.objects.filter(order__in=[r["order"] for r in RANKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ranks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_ranks, remove_ranks),
    ]
