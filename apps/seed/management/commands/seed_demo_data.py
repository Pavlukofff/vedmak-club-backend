import io
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image

from apps.accounts.models import AvatarPreset, CurrencyTransfer, SiteSettings, User
from apps.battles.models import Battle
from apps.bestiary.models import Bestiary, MonsterKill
from apps.blog.models import BlogPost, Festival, FestivalPhoto
from apps.codex.models import ClubCodex
from apps.faq.models import FAQItem
from apps.fundraisers.models import Fundraiser, FundraiserContribution
from apps.penalties.models import Penalty
from apps.ranks.models import Rank
from apps.schedule.models import ScheduleEntry
from apps.schools.models import School
from apps.shop.models import Purchase, ShopItem
from apps.subscriptions.models import ActivityPrice
from apps.tasks.models import TaskAssignment, TaskTemplate
from apps.titles.models import Title, TitleAward
from apps.tournaments.bracket import generate_bracket
from apps.tournaments.models import Tournament, TournamentMatch, TournamentParticipant, TournamentPhoto

DEMO_PASSWORD = "Demo12345!"
ADMIN_PASSWORD = "AdminDemo123!"


def placeholder_image(color, name):
    buffer = io.BytesIO()
    Image.new("RGB", (240, 160), color=color).save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=name)


class Command(BaseCommand):
    """Наполняет базу связной демо-данными по всем приложениям — для ручного

    тестирования и подключения фронтенда. Рассчитана на запуск сразу после
    'migrate' на чистой базе (сид-миграции школ/рангов/магазина/абонементов/
    групп уже применены); повторные запуски безопасны — везде get_or_create.
    """

    help = "Наполняет базу демо-данными по всем приложениям (только для DEBUG)"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_data предназначена только для DEBUG=True (локальная/тестовая среда).")

        with transaction.atomic():
            self.stdout.write("Настройки сайта...")
            self._seed_site_settings()

            self.stdout.write("Аватар-пресеты...")
            self._seed_avatar_presets()

            self.stdout.write("Пользователи...")
            users = self._seed_users()

            self.stdout.write("Роли и права...")
            self._seed_groups_and_permissions(users)

            self.stdout.write("Бестиарий...")
            bestiary = self._seed_bestiary()

            self.stdout.write("Титулы...")
            self._seed_titles(users)

            self.stdout.write("Задания...")
            self._seed_tasks(users)

            self.stdout.write("Заявки на смену ника/ранга...")
            self._seed_requests(users)

            self.stdout.write("Бои...")
            self._seed_battles(users)

            self.stdout.write("Убийства монстров...")
            self._seed_monster_kills(users, bestiary)

            self.stdout.write("Взыскания...")
            self._seed_penalties(users)

            self.stdout.write("Турниры...")
            self._seed_tournaments(users)

            self.stdout.write("Блог и фестивали...")
            self._seed_blog_and_festival(users)

            self.stdout.write("Расписание...")
            self._seed_schedule()

            self.stdout.write("Кодекс цеха...")
            self._seed_codex(users)

            self.stdout.write("Соц-сети...")
            self._seed_social_links(users)

            self.stdout.write("Сбор средств...")
            self._seed_fundraiser(users)

            self.stdout.write("Переводы кронов...")
            self._seed_currency_transfers(users)

            self.stdout.write("Покупки в магазине...")
            self._seed_purchases(users)

            self.stdout.write("FAQ...")
            self._seed_faq()

        self.stdout.write(self.style.SUCCESS("Готово."))
        self.stdout.write(f"Суперпользователь: admin / {ADMIN_PASSWORD}")
        self.stdout.write(f"Остальные демо-пользователи: <username> / {DEMO_PASSWORD}")

    # ------------------------------------------------------------------ #

    def _seed_site_settings(self):
        settings_obj = SiteSettings.load()
        settings_obj.starting_balance = 10
        settings_obj.save()

    def _seed_users(self):
        admin, admin_created = User.objects.get_or_create(
            username="admin",
            defaults=dict(email="admin@vedmak.club", display_name="Админ сайта", email_verified=True),
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.email_verified = True
        admin.set_password(ADMIN_PASSWORD)
        admin.save()

        today = timezone.localdate()
        roster = [
            dict(
                username="geralt", display_name="Геральт из Ривии", school="Школа Волка", rank=7,
                level=70, experience=5200, balance=320, email_verified=True,
                character_description="Ведьмак из школы Волка, охотник на чудовищ, немногословен.",
                name_visibility="public", birth_date=today.replace(year=today.year - 90),
            ),
            dict(
                username="yennefer", display_name="Йеннифэр из Венгерберга", school="Школа Мантикоры", rank=5,
                level=60, experience=4100, balance=410, email_verified=True,
                character_description="Чародейка, alchемик и советник клуба.",
                name_visibility="public", birth_date=today + timedelta(days=2),
                birth_date_visibility="day_month",
            ),
            dict(
                username="ciri", display_name="Цири", school="Школа Кота", rank=6,
                level=55, experience=3300, balance=180, email_verified=True,
                character_description="Юная фехтовальщица школы Кота, быстрая и дерзкая.",
                name_visibility="public", birth_date=today + timedelta(days=5),
                birth_date_visibility="day_month",
            ),
            dict(
                username="triss", display_name="Трисс Меригольд", school="Школа Грифона", rank=4,
                level=40, experience=1900, balance=150, email_verified=True,
                character_description="Чародейка, помогает клубу с организацией фестивалей.",
                name_visibility="hidden", birth_date=today.replace(year=today.year - 30),
            ),
            dict(
                username="dandelion", display_name="Лютик", school=None, rank=2,
                level=15, experience=420, balance=600, email_verified=False,
                character_description="Бард, официальный летописец клуба, в боях участвует редко.",
                name_visibility="public", birth_date=today.replace(year=today.year - 35),
            ),
            dict(
                username="vesemir", display_name="Весемир", school="Школа Волка", rank=8,
                level=95, experience=9000, balance=250, email_verified=True,
                character_description="Старший мастер школы Волка, учитель всех местных ведьмаков.",
                name_visibility="public", birth_date=today.replace(year=today.year - 120),
            ),
            dict(
                username="lambert", display_name="Ламберт", school="Школа Волка", rank=7,
                level=68, experience=5000, balance=140, email_verified=True,
                character_description="Едкий на язык ведьмак школы Волка.",
                name_visibility="hidden", birth_date=today.replace(year=today.year - 45),
            ),
            dict(
                username="eskel", display_name="Эскель", school="Школа Волка", rank=7,
                level=66, experience=4800, balance=160, email_verified=True,
                character_description="Спокойный и рассудительный ведьмак школы Волка.",
                name_visibility="hidden", birth_date=today.replace(year=today.year - 44),
            ),
            dict(
                username="zoltan", display_name="Золтан Хивай", school=None, rank=3,
                level=25, experience=800, balance=90, email_verified=True,
                character_description="Гном, боец и хороший друг клуба.",
                name_visibility="public", birth_date=today.replace(year=today.year - 50),
            ),
            dict(
                username="milva", display_name="Мильва", school="Школа Лисы", rank=4,
                level=38, experience=1700, balance=200, email_verified=True,
                character_description="Лучница школы Лисы, меткая и немногословная.",
                name_visibility="public", birth_date=today.replace(year=today.year - 33),
            ),
        ]

        users = {"admin": admin}
        for row in roster:
            username = row["username"]
            school = School.objects.get(name=row["school"]) if row["school"] else None
            rank = Rank.objects.get(order=row["rank"])
            field_values = dict(
                email=f"{username}@vedmak.club",
                display_name=row["display_name"],
                school=school,
                rank=rank,
                level=row["level"],
                experience=row["experience"],
                balance=row["balance"],
                email_verified=row["email_verified"],
                character_description=row["character_description"],
                name_visibility=row["name_visibility"],
                birth_date=row["birth_date"],
                birth_date_visibility=row.get("birth_date_visibility", "hidden"),
            )
            # Реальные значения передаются в defaults, чтобы при создании
            # сигнал регистрации не назначал их отдельным (видимым в ленте
            # дашборда) вторым save() — только дефолтный аватар.
            user, created = User.objects.get_or_create(username=username, defaults=field_values)
            if not created:
                for field, value in field_values.items():
                    setattr(user, field, value)
                # При повторном запуске команды это тоже не «реальное»
                # изменение ранга/баланса — подавляем шум в ленте дашборда.
                user._is_registration_default_save = True
            user.set_password(DEMO_PASSWORD)
            user.save()
            # _is_registration_default_save — разовая метка на save() внутри
            # сигнала регистрации; объект пользователя переиспользуется по
            # всему скрипту дальше, так что метку нужно снять, иначе она
            # заглушит легитимные начисления (например, за убийство монстра)
            # в остальных _seed_* методах.
            if hasattr(user, "_is_registration_default_save"):
                del user._is_registration_default_save
            users[username] = user

        return users

    def _seed_groups_and_permissions(self, users):
        def perm(app_label, codename):
            return Permission.objects.get(content_type__app_label=app_label, codename=codename)

        master_group, _ = Group.objects.get_or_create(name="Мастер школы")
        master_group.permissions.set([
            perm("tasks", "can_manage_tasks"),
            perm("bestiary", "can_record_kills"),
            perm("titles", "can_grant_titles"),
            perm("schedule", "can_manage_schedule"),
            perm("shop", "can_grant_items"),
        ])
        users["vesemir"].groups.add(master_group)
        users["vesemir"].is_staff = True
        users["vesemir"].save(update_fields=["is_staff"])

        dgk_group, _ = Group.objects.get_or_create(name="Десница Главы Клуба")
        dgk_group.permissions.set([
            perm("penalties", "can_issue_penalties"),
            perm("battles", "can_record_battles"),
        ])
        users["geralt"].groups.add(dgk_group)
        users["geralt"].is_staff = True
        users["geralt"].save(update_fields=["is_staff"])

        gk_group, _ = Group.objects.get_or_create(name="Глава Клуба")
        gk_group.permissions.set([
            perm("penalties", "can_cancel_penalties"),
            perm("penalties", "can_view_penalties"),
            perm("ranks", "can_approve_ranks"),
            perm("accounts", "can_review_displayname_requests"),
            perm("tournaments", "can_manage_tournaments"),
            perm("fundraisers", "can_manage_fundraisers"),
            perm("social", "can_manage_social_links"),
            perm("blog", "can_manage_blog"),
            perm("blog", "can_manage_festivals"),
        ])
        users["yennefer"].groups.add(gk_group)
        users["yennefer"].is_staff = True
        users["yennefer"].save(update_fields=["is_staff"])

    def _seed_avatar_presets(self):
        presets = [
            ("Герб школы Волка", "школы ведьмаков", (60, 60, 70)),
            ("Герб школы Кота", "школы ведьмаков", (90, 70, 40)),
            ("Силуэт грифона", "монстры", (70, 90, 110)),
        ]
        for title, category, color in presets:
            if AvatarPreset.objects.filter(title=title).exists():
                continue
            preset = AvatarPreset(title=title, category=category)
            preset.image.save(f"{title}.png", placeholder_image(color, f"{title}.png"), save=True)

    def _seed_bestiary(self):
        species = [
            ("Утопец", "низший вид", "low", "Утопленник, поднявшийся из воды после смерти в реке или озере."),
            ("Накер", "низший вид", "low", "Мелкий гуманоид-падальщик, обитающий стаями в пещерах."),
            ("Гуль", "низший вид", "medium", "Падальщик, питается трупами на местах недавних сражений."),
            ("Кикимора", "гибрид", "medium", "Болотное чудовище с хитиновым панцирем и длинными лапами."),
            ("Грифон", "реликт", "high", "Крылатый хищник, охраняющий горные перевалы."),
            ("Леший", "проклятье", "deadly", "Древний дух леса, насылающий морок на случайных путников."),
        ]
        result = {}
        for name, category, danger, description in species:
            obj, _ = Bestiary.objects.get_or_create(
                name=name, defaults=dict(category=category, danger_level=danger, description=description),
            )
            result[name] = obj
        return result

    def _seed_titles(self, users):
        titles = [
            ("Победитель Кубка цеха", "Занял 1 место в официальном турнире клуба"),
            ("Гроза чудовищ", "5 и более подтверждённых убийств из бестиария"),
            ("Хранитель традиций", "Многолетний вклад в жизнь цеха"),
            ("Друг клуба", "Существенная помощь в организации мероприятий"),
        ]
        title_objs = {}
        for name, description in titles:
            obj, _ = Title.objects.get_or_create(name=name, defaults=dict(description=description))
            title_objs[name] = obj

        awards = [
            ("vesemir", "Хранитель традиций", "Более 15 лет во главе школы Волка"),
            ("geralt", "Гроза чудовищ", "12 подтверждённых убийств в бестиарии"),
            ("dandelion", "Друг клуба", "Организация летнего фестиваля клинка"),
        ]
        for username, title_name, reason in awards:
            TitleAward.objects.get_or_create(
                user=users[username], title=title_objs[title_name],
                defaults=dict(reason=reason, granted_by=users["admin"]),
            )

    def _seed_tasks(self, users):
        templates = [
            dict(
                title="Победить 3 утопцев", description="Очистить прибрежную заводь от утопцев.",
                requirements="Разрешение мастера школы, ранг не ниже «Ученик цеха».",
                reward_experience=40, reward_currency=25, max_slots=3, is_repeatable=False,
            ),
            dict(
                title="Тренировка на выносливость", description="10 повторов силового упражнения на тренировке.",
                requirements="Без ограничений.", reward_experience=10, reward_currency=5,
                max_slots=None, is_repeatable=True,
            ),
            dict(
                title="Испытание травами", description="Пройти испытание травами для допуска к Знакам.",
                requirements="Уровень не ниже 25.", reward_experience=30, reward_currency=0,
                max_slots=None, is_repeatable=False,
            ),
            dict(
                title="Охота на лешего", description="Выследить и одолеть лешего в дальнем лесу.",
                requirements="Только для «Признанных Ведьмаков» и выше, в группе не менее 2 человек.",
                reward_experience=80, reward_currency=60, max_slots=1, is_repeatable=False,
            ),
        ]
        template_objs = {}
        for row in templates:
            obj, _ = TaskTemplate.objects.get_or_create(title=row["title"], defaults=row)
            template_objs[row["title"]] = obj

        if not TaskAssignment.objects.filter(user=users["ciri"], task_template=template_objs["Тренировка на выносливость"]).exists():
            TaskAssignment.objects.create(
                user=users["ciri"], task_template=template_objs["Тренировка на выносливость"],
                status=TaskAssignment.Status.COMPLETED,
            )
        if not TaskAssignment.objects.filter(user=users["triss"], task_template=template_objs["Победить 3 утопцев"]).exists():
            TaskAssignment.objects.create(
                user=users["triss"], task_template=template_objs["Победить 3 утопцев"],
                status=TaskAssignment.Status.IN_PROGRESS,
            )
        if not TaskAssignment.objects.filter(user=users["dandelion"], task_template=template_objs["Тренировка на выносливость"]).exists():
            TaskAssignment.objects.create(
                user=users["dandelion"], task_template=template_objs["Тренировка на выносливость"],
                status=TaskAssignment.Status.CANCELLED,
            )

    def _seed_requests(self, users):
        from apps.accounts.models import DisplayNameChangeRequest
        from apps.ranks.models import RankUpRequest

        # Одна заявка "на рассмотрении" и одна уже одобренная — чтобы в
        # демо-данных были оба состояния и вся цепочка событий в ленте.
        DisplayNameChangeRequest.objects.get_or_create(
            user=users["milva"], requested_name="Мария Барринг",
            defaults=dict(current_name=users["milva"].display_name, reason="Хочу настоящее имя в профиле"),
        )
        approved_name_request, created = DisplayNameChangeRequest.objects.get_or_create(
            user=users["lambert"], requested_name="Ламберт из Курлибрена",
            defaults=dict(
                current_name=users["lambert"].display_name, reason="Хочу указать родину персонажа",
            ),
        )
        if created:
            approved_name_request.status = DisplayNameChangeRequest.Status.APPROVED
            approved_name_request.reviewed_by = users["yennefer"]
            approved_name_request.reviewed_at = timezone.now()
            approved_name_request.save()
            users["lambert"].display_name = approved_name_request.requested_name
            users["lambert"].save(update_fields=["display_name"])

        RankUpRequest.objects.get_or_create(
            user=users["zoltan"], to_rank=Rank.objects.get(order=4),
            defaults=dict(from_rank=users["zoltan"].rank, comment="Выполнил все требования по бою и квестам"),
        )
        approved_rank_request, created = RankUpRequest.objects.get_or_create(
            user=users["milva"], to_rank=Rank.objects.get(order=5),
            defaults=dict(from_rank=users["milva"].rank, comment="Прошла испытание травами и поиск святилищ"),
        )
        if created:
            approved_rank_request.status = RankUpRequest.Status.APPROVED
            approved_rank_request.reviewed_by = users["yennefer"]
            approved_rank_request.reviewed_at = timezone.now()
            approved_rank_request.save()
            users["milva"].rank = approved_rank_request.to_rank
            users["milva"]._activity_actor = users["yennefer"]
            users["milva"].save(update_fields=["rank"])

    def _seed_battles(self, users):
        pairs = [
            ("geralt", "lambert", "geralt", "ТС", False, None),
            ("eskel", "ciri", "eskel", "ТС", False, None),
            ("triss", "milva", "milva", "ТС", False, None),
            ("zoltan", "dandelion", "zoltan", "ТС", False, None),
            ("geralt", "eskel", "geralt", "РС", True, "vesemir"),
            ("ciri", "milva", "ciri", "РС", False, None),
            ("lambert", "zoltan", "lambert", "ТС", False, None),
        ]
        for f1, f2, winner, battle_type, is_ranked, judge in pairs:
            if Battle.objects.filter(fighter1=users[f1], fighter2=users[f2], type=battle_type).exists():
                continue
            Battle.objects.create(
                type=battle_type, fighter1=users[f1], fighter2=users[f2], winner=users[winner],
                is_ranked=is_ranked, main_judge=users[judge] if judge else None,
                recorded_by=users["admin"], notes="Демо-данные для тестирования.",
            )

    def _seed_monster_kills(self, users, bestiary):
        kills = [
            ("geralt", "Утопец", True, 20, 15),
            ("geralt", "Накер", True, 15, 10),
            ("ciri", "Кикимора", True, 35, 20),
            ("lambert", "Гуль", False, None, None),
            ("vesemir", "Грифон", True, 60, 40),
            ("eskel", "Утопец", False, None, None),
        ]
        for username, species, granted, exp, currency in kills:
            user = users[username]
            species_obj = bestiary[species]
            if MonsterKill.objects.filter(user=user, bestiary=species_obj).exists():
                continue
            MonsterKill.objects.create(
                user=user, bestiary=species_obj, recorded_by=users["vesemir"],
                notes="Охота зафиксирована мастером школы.",
                reward_granted=granted,
                reward_granted_by=users["vesemir"] if granted else None,
                reward_experience=exp, reward_currency=currency,
            )

    def _seed_penalties(self, users):
        penalty, created = Penalty.objects.get_or_create(
            user=users["dandelion"], type=Penalty.Type.REMARK,
            reason="Опоздание на тренировку без предупреждения.",
            defaults=dict(issued_by=users["geralt"]),
        )

        cancelled, created = Penalty.objects.get_or_create(
            user=users["zoltan"], type=Penalty.Type.BATTLE_REMARK,
            reason="Удар после команды «стоп» на тренировочном бою.",
            defaults=dict(issued_by=users["geralt"]),
        )
        if cancelled.status != Penalty.Status.CANCELLED:
            cancelled.status = Penalty.Status.CANCELLED
            cancelled.cancelled_by = users["yennefer"]
            cancelled.cancel_reason = "Разобрались — сигнал остановки не был услышан из-за шума."
            cancelled.cancelled_at = timezone.now()
            cancelled.save()

    def _seed_tournaments(self, users):
        today = timezone.localdate()

        Tournament.objects.get_or_create(
            title="Осенний турнир новичков",
            defaults=dict(
                description="Турнир для тех, кто впервые выходит на ранговый бой.",
                date_start=today + timedelta(days=30),
                status=Tournament.Status.UPCOMING,
            ),
        )

        cup, created = Tournament.objects.get_or_create(
            title="Кубок цеха",
            defaults=dict(
                description="Главный ежегодный турнир клуба, двойное выбывание.",
                date_start=today - timedelta(days=10),
                status=Tournament.Status.FINISHED,
                bracket_type=Tournament.BracketType.DOUBLE,
            ),
        )
        if not created or cup.bracket_generated:
            return

        seeds = [("geralt", 1), ("vesemir", 2), ("yennefer", 3), ("ciri", 4)]
        for username, seed in seeds:
            TournamentParticipant.objects.create(tournament=cup, user=users[username], seed=seed)

        generate_bracket(cup)

        from apps.dashboard.models import ActivityLogEntry

        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.BRACKET_GENERATED,
            actor=users["yennefer"],
            related_object_id=str(cup.pk),
            message=f"{users['yennefer'].display_name}: сгенерировал(а) сетку турнира «{cup.title}»",
        )

        def play(bracket, round_number, position, fighter1, fighter2, winner, is_ranked=False, judge=None):
            match = TournamentMatch.objects.get(
                tournament=cup, bracket=bracket, round_number=round_number, position=position,
            )
            battle = Battle.objects.create(
                type="РС", fighter1=users[fighter1], fighter2=users[fighter2], winner=users[winner],
                is_ranked=is_ranked, main_judge=users[judge] if judge else None,
                recorded_by=users["admin"], tournament=cup, notes="Матч турнира «Кубок цеха».",
            )
            match.battle = battle
            match.save()

        play(TournamentMatch.Bracket.UPPER, 1, 0, "geralt", "ciri", "geralt")
        play(TournamentMatch.Bracket.UPPER, 1, 1, "vesemir", "yennefer", "yennefer")
        play(TournamentMatch.Bracket.LOWER, 1, 0, "ciri", "vesemir", "vesemir")
        play(TournamentMatch.Bracket.UPPER, 2, 0, "geralt", "yennefer", "yennefer", is_ranked=True, judge="vesemir")
        play(TournamentMatch.Bracket.LOWER, 2, 0, "vesemir", "geralt", "geralt")
        play(TournamentMatch.Bracket.FINAL, 1, 0, "yennefer", "geralt", "geralt", is_ranked=True, judge="vesemir")

        for caption, color in [("Финальный матч", (120, 40, 40)), ("Награждение победителя", (40, 90, 60))]:
            photo = TournamentPhoto(tournament=cup, caption=caption)
            photo.image.save(f"{caption}.png", placeholder_image(color, f"{caption}.png"), save=True)

    def _seed_blog_and_festival(self, users):
        today = timezone.localdate()
        festival, _ = Festival.objects.get_or_create(
            title="Летний фестиваль клинка",
            defaults=dict(
                description="Ежегодный сбор клуба с показательными боями и мастер-классами.",
                date_start=today - timedelta(days=60), date_end=today - timedelta(days=58),
            ),
        )
        if not festival.photos.exists():
            for caption, color in [("Открытие фестиваля", (80, 60, 110)), ("Показательный бой", (110, 80, 40))]:
                photo = FestivalPhoto(festival=festival, caption=caption)
                photo.image.save(f"{caption}.png", placeholder_image(color, f"{caption}.png"), save=True)

        posts = [
            dict(
                title="Итоги Летнего фестиваля клинка",
                content="В этом году фестиваль собрал рекордное число участников. Спасибо всем, кто пришёл!",
                festival=festival, author="yennefer", is_published=True,
            ),
            dict(
                title="Открыт набор в школу Кота",
                content="Школа Кота набирает учеников на новый сезон. Записывайтесь через личный кабинет.",
                festival=None, author="vesemir", is_published=True,
            ),
            dict(
                title="Черновик анонса зимнего турнира",
                content="Планируем зимний турнир, детали уточняются.",
                festival=None, author="admin", is_published=False,
            ),
        ]
        for row in posts:
            BlogPost.objects.get_or_create(
                title=row["title"],
                defaults=dict(
                    content=row["content"], festival=row["festival"],
                    author=users[row["author"]], is_published=row["is_published"],
                ),
            )

    def _seed_schedule(self):
        def activity(name):
            return ActivityPrice.objects.filter(name=name).first()

        entries = [
            (0, "18:00", "20:00", "Фехтовальная тренировка", activity("Фехтовальная тренировка"), "Зал №1"),
            (1, "19:00", "21:00", "Стрельба из лука", activity("Стрельба из лука"), "Тир"),
            (3, "18:30", "20:30", "Метание ножей", activity("Метание ножей"), "Зал №2"),
            (5, "12:00", "14:00", "Файер-тренировка", activity("Файер-тренировка"), "Двор"),
            (6, "16:00", "17:00", "Общий сбор клуба", None, "Зал №1"),
            (2, "18:00", "20:00", "Старое занятие (снято с расписания)", None, "Зал №1"),
        ]
        for weekday, start, end, title, act, location in entries:
            ScheduleEntry.objects.get_or_create(
                title=title,
                defaults=dict(
                    weekday=weekday, start_time=start, end_time=end, activity=act,
                    location=location, is_active=(title != "Старое занятие (снято с расписания)"),
                ),
            )

    def _seed_codex(self, users):
        codex = ClubCodex.load()
        if codex.content:
            return
        codex.content = (
            "Кодекс цеха ведьмаков.\n\n"
            "Глава 1. Общие положения.\n"
            "Цех объединяет фехтовальщиков, разделяющих интерес к вселенной «Ведьмак» "
            "и живой фехтовальной отыгровке. Членство в цехе добровольное.\n\n"
            "Глава 2. Иерархия.\n"
            "Рекрут -> Ученик -> Бронзовый кандидат -> Серебряный кандидат -> "
            "Золотой кандидат -> Младший ведьмак -> Признанный Ведьмак -> Мастер Ведьмак.\n\n"
            "Глава 3. Дисциплина.\n"
            "Взыскания выносятся уполномоченными ролями по регламенту клуба."
        )
        codex.updated_by = users["admin"]
        codex.save()

    def _seed_social_links(self, users):
        links = [
            ("club", None, "Telegram", "https://t.me/vedmak_club", "Новости клуба"),
            ("club", None, "VK", "https://vk.com/vedmak_club", ""),
            ("armory", None, "Instagram", "https://instagram.com/vedmak_armory", "Оружейня клуба"),
            ("master", "vesemir", "Telegram", "https://t.me/vesemir_wolf_school", "Школа Волка"),
            ("master", "triss", "Instagram", "https://instagram.com/triss_griffin_school", "Школа Грифона"),
        ]
        from apps.social.models import SocialLink

        for owner_type, owner_username, platform, url, label in links:
            SocialLink.objects.get_or_create(
                owner_type=owner_type, platform=platform,
                owner=users[owner_username] if owner_username else None,
                defaults=dict(url=url, label=label),
            )

    def _seed_fundraiser(self, users):
        fundraiser, _ = Fundraiser.objects.get_or_create(
            title="Новые клинки для младших ведьмаков",
            defaults=dict(
                description="Собираем на комплект тренировочного оружия для новых учеников.",
                goal_amount="1500.00", status=Fundraiser.Status.ACTIVE,
            ),
        )
        if fundraiser.contributions.exists():
            return

        FundraiserContribution.objects.create(
            fundraiser=fundraiser, contributor=users["geralt"], amount="50.00",
            recorded_by=users["yennefer"], comment="На доброе дело.",
        )
        FundraiserContribution.objects.create(
            fundraiser=fundraiser, contributor=users["triss"], amount="30.00",
            is_anonymous=True, recorded_by=users["yennefer"],
        )
        FundraiserContribution.objects.create(
            fundraiser=fundraiser, contributor_name="Друг клуба Богдан", amount="20.00",
            recorded_by=users["yennefer"],
        )

    def _seed_currency_transfers(self, users):
        if not CurrencyTransfer.objects.filter(sender=users["geralt"], recipient=users["dandelion"]).exists():
            CurrencyTransfer.objects.create(
                sender=users["geralt"], recipient=users["dandelion"], amount=15,
                message="За песню в мою честь.",
            )
        if not CurrencyTransfer.objects.filter(sender=users["triss"], recipient=users["yennefer"]).exists():
            CurrencyTransfer.objects.create(
                sender=users["triss"], recipient=users["yennefer"], amount=10,
                message="Возврат долга.",
            )

    def _seed_purchases(self, users):
        scroll = ShopItem.objects.filter(name="Свиток обновления").first()
        potion = ShopItem.objects.filter(name="Грач").first()

        if scroll and not Purchase.objects.filter(user=users["dandelion"], item=scroll).exists():
            Purchase.objects.create(user=users["dandelion"], item=scroll, price_paid=scroll.price)

        if potion and not Purchase.objects.filter(user=users["geralt"], item=potion).exists():
            Purchase.objects.create(user=users["geralt"], item=potion, granted_by=users["vesemir"])

    def _seed_faq(self):
        items = [
            ("Как вступить в клуб?", "Зарегистрируйтесь на сайте и приходите на тренировку.", "Регистрация", 1),
            ("Как купить абонемент?", "Абонементы продаются офлайн, на сайте — только витрина цен.", "Абонементы", 1),
            ("Что делать, если забыл пароль?", "Восстановление пароля доступно на странице входа.", "Аккаунт", 1),
            ("Как работает система рангов?", "Ранг присваивается по заявке после проверки требований мастером.", "Ранги", 1),
            ("Черновик — не публикуем", "Технический черновик для проверки видимости.", "", 99),
        ]
        for question, answer, category, order in items:
            FAQItem.objects.get_or_create(
                question=question,
                defaults=dict(answer=answer, category=category, order=order, is_active=(order != 99)),
            )
