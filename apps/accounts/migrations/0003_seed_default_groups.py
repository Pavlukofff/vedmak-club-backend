from django.db import migrations

# Роли по умолчанию из раздела 2 плана (иерархия клуба по Кодексу цеха).
# «Гость» не заводится — это неаутентифицированное состояние, не назначаемая роль.
DEFAULT_GROUPS = [
    "Участник",
    "Стажёр подмастерья",
    "Подмастерье",
    "Мастер школы",
    "Десница Главы Клуба",
    "Глава Клуба",
    "Админ сайта",
]


def seed_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in DEFAULT_GROUPS:
        Group.objects.get_or_create(name=name)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=DEFAULT_GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_groups, remove_groups),
    ]
