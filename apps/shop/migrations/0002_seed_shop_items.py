from django.db import migrations

# Раздел 4.8 плана — типы эффектов из документа (расширяемый справочник).
EFFECT_TYPES = [
    ("hp", "Максимальное ХП"),
    ("damage", "Урон"),
    ("sign_slot", "Слот знака"),
    ("sign_power", "Сила знака"),
    ("poison_resist", "Сопротивление яду"),
    ("aksiy_resist", "Сопротивление Аксию"),
    ("regen", "Регенерация"),
    ("task_add", "Доп. квест"),
    ("task_repeat", "Повтор квеста"),
    ("task_summon", "Призыв квеста"),
    ("task_refresh", "Обновление квеста"),
    ("task_retry", "Повторная попытка квеста"),
]

# Реальный список эликсиров из документа «Своё Дело» (раздел 4.8 плана).
# Цена не указана в документе — эликсиры крафтятся мастером-алхимиком за
# рецепт/кроны/трофеи, а не покупаются за фиксированную цену (price=None).
POTIONS = [
    dict(name="Грач", min_rank="Серебряный кандидат цеха", toxicity="30%",
         description="+1 к урону клинка",
         effect=dict(type="damage", value=1, duration="permanent")),
    dict(name="Новолуние", min_rank="Серебряный кандидат цеха", toxicity="30%",
         description="+2 к макс. ХП",
         effect=dict(type="hp", value=2, duration="permanent")),
    dict(name="Чаша Вильгефорца", min_rank="Серебряный кандидат цеха", toxicity="30%",
         description="+1 слот для использования знаков",
         effect=dict(type="sign_slot", value=1, duration="permanent")),
    dict(name="Филин", min_rank="Серебряный кандидат цеха", toxicity="30%",
         description="+1 сила знаков",
         effect=dict(type="sign_power", value=1, duration="permanent")),
    dict(name="Ласточка", min_rank="Серебряный кандидат цеха",
         toxicity="0% за первую, 30% за каждую следующую",
         description="Следующие 5 тактов боя восстанавливают 1 хит, суммируется",
         effect=dict(type="regen", value=1, duration="temporary", duration_value=5)),
    dict(name="Иволга 1 ур.", min_rank="Серебряный кандидат цеха",
         toxicity="0% за первую, 30% за каждую следующую",
         description="Игнорирует/снимает 1 яд",
         effect=dict(type="poison_resist", value=1, duration="permanent")),
    dict(name="Иволга 2 ур.", min_rank="Признанный Ведьмак", toxicity="45%",
         description="Игнорирует/снимает 2 яда",
         effect=dict(type="poison_resist", value=2, duration="permanent")),
    dict(name="Волк 1 ур.", min_rank="Младший ведьмак школы", toxicity="45%",
         description="Попадание в корпус — на 1 ед. урона больше",
         effect=dict(type="damage", value=1, duration="permanent")),
    dict(name="Волк 2 ур.", min_rank="Признанный Ведьмак", toxicity="45%",
         description="Попадание в корпус — на 2 ед. урона больше",
         effect=dict(type="damage", value=2, duration="permanent")),
    dict(name="Гром 1 ур.", min_rank="Младший ведьмак школы", toxicity="45%",
         description="Урон клинка +2, входящий урон +1",
         effect=dict(type="damage", value=2, duration="permanent")),
    dict(name="Гром 2 ур.", min_rank="Признанный Ведьмак", toxicity="60%",
         description="Урон клинка +3, входящий урон +1",
         effect=dict(type="damage", value=3, duration="permanent")),
    dict(name="Ива 1 ур.", min_rank="Младший ведьмак школы", toxicity="45%",
         description="Игнорирует 1 Аксий",
         effect=dict(type="aksiy_resist", value=1, duration="permanent")),
    dict(name="Ива 2 ур.", min_rank="Признанный Ведьмак", toxicity="60%",
         description="Игнорирует 2 Аксия",
         effect=dict(type="aksiy_resist", value=2, duration="permanent")),
    dict(name="Кряква", min_rank="Младший ведьмак школы", toxicity="30%",
         description=(
             "Спец-эффект: -1 урон клинка и -1 слот знака, но +1 хп каждые "
             "10 тактов; особый эффект при 0 слотов/уроне 1"
         ),
         effect=None),
    dict(name="Вирга 1 ур.", min_rank="Младший ведьмак школы", toxicity="45%",
         description="Игнорирует 1 знак на базе Игни или 1 яд",
         effect=None),
    dict(name="Вирга 2 ур.", min_rank="Признанный Ведьмак", toxicity="60%",
         description="Игнорирует 2 знака на базе Игни или 2 яда",
         effect=None),
]

# Реальный список свитков из документа «Своё Дело» (раздел 4.8 плана).
SCROLLS = [
    dict(name="Свиток дополнения", price=100,
         description="Позволяет выполнить ещё 1 квест на тренировке"),
    dict(name="Свиток повтора", price=200,
         description="Позволяет повторно выполнить любой квест"),
    dict(name="Свиток вызова", price=50,
         description="Позволяет призвать любой квест, даже если его нет на доске"),
    dict(name="Свиток обновления", price=10,
         description="Заменяет квест в руке на случайный, ещё не выполненный"),
    dict(name="Свиток попытки", price=50,
         description=(
             "Позволяет повторно попытаться выполнить провальный квест "
             "(кроме отдельных долгих квестов вроде «Тишина»)"
         )),
]


def seed(apps, schema_editor):
    EffectType = apps.get_model("shop", "EffectType")
    ShopItem = apps.get_model("shop", "ShopItem")
    ItemEffect = apps.get_model("shop", "ItemEffect")
    Rank = apps.get_model("ranks", "Rank")

    effect_types = {}
    for code, name in EFFECT_TYPES:
        et, _ = EffectType.objects.update_or_create(code=code, defaults={"name": name})
        effect_types[code] = et

    ranks_by_name = {r.name: r for r in Rank.objects.all()}

    for potion in POTIONS:
        item, _ = ShopItem.objects.update_or_create(
            name=potion["name"],
            defaults=dict(
                category="potion",
                description=potion["description"],
                toxicity=potion["toxicity"],
                min_rank=ranks_by_name.get(potion["min_rank"]),
                price=None,
            ),
        )
        item.effects.all().delete()
        effect = potion["effect"]
        if effect:
            ItemEffect.objects.create(
                item=item,
                type=effect_types[effect["type"]],
                value=effect.get("value"),
                duration=effect.get("duration", "instant"),
                duration_value=effect.get("duration_value"),
            )

    for scroll in SCROLLS:
        ShopItem.objects.update_or_create(
            name=scroll["name"],
            defaults=dict(
                category="scroll",
                description=scroll["description"],
                price=scroll["price"],
            ),
        )


def unseed(apps, schema_editor):
    ShopItem = apps.get_model("shop", "ShopItem")
    EffectType = apps.get_model("shop", "EffectType")
    names = [p["name"] for p in POTIONS] + [s["name"] for s in SCROLLS]
    ShopItem.objects.filter(name__in=names).delete()
    EffectType.objects.filter(code__in=[code for code, _ in EFFECT_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0001_initial"),
        ("ranks", "0002_seed_ranks"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
