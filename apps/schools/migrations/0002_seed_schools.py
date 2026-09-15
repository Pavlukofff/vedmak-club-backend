from django.db import migrations

SCHOOLS = [
    dict(
        name="Школа Волка",
        weapon_type="Полуторный меч",
        base_hp=10,
        base_damage="1",
        sign_slots=3,
        intoxication_threshold=100,
        special_abilities="Может использовать 1 эликсир дважды",
        status="active",
    ),
    dict(
        name="Школа Мантикоры",
        weapon_type="Стафф",
        base_hp=10,
        base_damage="1",
        sign_slots=2,
        intoxication_threshold=130,
        special_abilities="",
        status="active",
    ),
    dict(
        name="Школа Медведя",
        weapon_type="Цвайхандер",
        base_hp=15,
        base_damage="1",
        sign_slots=2,
        intoxication_threshold=100,
        special_abilities="",
        status="active",
    ),
    dict(
        name="Школа Кота",
        weapon_type="Парные короткие одноручные мечи",
        base_hp=8,
        base_damage="2",
        sign_slots=3,
        intoxication_threshold=100,
        special_abilities="Попадание в торс наносит на 1 ед. больше урона",
        status="active",
    ),
    dict(
        name="Школа Змеи",
        weapon_type="Катана",
        base_hp=10,
        base_damage="1",
        sign_slots=3,
        intoxication_threshold=100,
        special_abilities=(
            "Использование ядов; выбор одной из 2 веток развития "
            "(мастерство ядов / использование фамильяра)"
        ),
        status="active",
    ),
    dict(
        name="Школа Грифона",
        weapon_type="Баклер + деревянный меч",
        base_hp=10,
        base_damage="0",
        sign_slots=4,
        intoxication_threshold=100,
        special_abilities=(
            "Может восстанавливать использование Знаков; "
            "урон оружия эликсирами не увеличивается"
        ),
        status="active",
    ),
    dict(
        name="Школа Лисы",
        weapon_type="Лук + одноручный меч",
        base_hp=8,
        base_damage="лук 2–3 (растёт с дистанцией), меч 1",
        sign_slots=2,
        intoxication_threshold=100,
        special_abilities=(
            "Колчан по умолчанию на 3 стрелы; урон лука не увеличивается "
            "эликсирами; можно покупать стрелы с эффектами"
        ),
        status="active",
    ),
    dict(
        name="Школа Россомахи",
        weapon_type="Два топора",
        base_hp=None,
        base_damage="",
        sign_slots=None,
        intoxication_threshold=None,
        special_abilities="В разработке, параметры пока не заданы",
        status="in_development",
    ),
]


def seed_schools(apps, schema_editor):
    School = apps.get_model("schools", "School")
    for data in SCHOOLS:
        School.objects.update_or_create(name=data["name"], defaults=data)


def remove_schools(apps, schema_editor):
    School = apps.get_model("schools", "School")
    School.objects.filter(name__in=[s["name"] for s in SCHOOLS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_schools, remove_schools),
    ]
