from django.conf import settings
from django.db import models
from django.db.models import Max


class Tournament(models.Model):
    """Турнир — упомянут в разделах 1 и 4.14 плана, но без собственной схемы.

    Контейнер для сетки на выбывание (TournamentParticipant/TournamentMatch).
    Сайт не рассчитывает сами бои — только переносит по сетке уже
    зафиксированный судьёй результат связанного Battle.

    bracket_type=double: верхняя сетка идёт своим чередом до своего финала;
    проигравшие после первого поражения падают в нижнюю сетку; победитель
    нижней встречается с победителем верхней в одном решающем матче за
    1-2 место (без bracket reset).
    """

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Предстоит"
        ONGOING = "ongoing", "Идёт"
        FINISHED = "finished", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    class BracketType(models.TextChoices):
        SINGLE = "single", "Одиночное выбывание"
        DOUBLE = "double", "Двойное выбывание (с нижней сеткой)"

    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    date_start = models.DateField("дата начала")
    date_end = models.DateField("дата окончания", blank=True, null=True)
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.UPCOMING,
    )
    bracket_type = models.CharField(
        "формат сетки", max_length=10, choices=BracketType.choices, default=BracketType.SINGLE,
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="победитель (1 место)",
        related_name="tournaments_won", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Проставляется автоматически по итогам финального матча",
    )
    runner_up = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="второе место",
        related_name="tournaments_runner_up", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Проставляется автоматически — проигравший финального матча",
    )
    results_notes = models.TextField("итоги/примечания", blank=True)
    bracket_generated = models.BooleanField("сетка сгенерирована", default=False)

    class Meta:
        verbose_name = "турнир"
        verbose_name_plural = "турниры"
        ordering = ["-date_start"]
        permissions = [
            ("can_manage_tournaments", "Может управлять участниками, сеткой и результатами турниров"),
        ]

    def __str__(self):
        return self.title

    def upper_bracket_rounds(self):
        return self.matches.filter(bracket=TournamentMatch.Bracket.UPPER).aggregate(
            n=Max("round_number"),
        )["n"] or 0

    def lower_bracket_rounds(self):
        r = self.upper_bracket_rounds()
        return max(0, 2 * (r - 1))


class TournamentPhoto(models.Model):
    """Фото прошедшего турнира — архив с фотографиями (раздел 1 плана)."""

    tournament = models.ForeignKey(
        Tournament, verbose_name="турнир", related_name="photos", on_delete=models.CASCADE,
    )
    image = models.ImageField("изображение", upload_to="tournaments/")
    caption = models.CharField("подпись", max_length=200, blank=True)

    class Meta:
        verbose_name = "фото турнира"
        verbose_name_plural = "фото турнира"
        ordering = ["id"]

    def __str__(self):
        return self.caption or f"Фото #{self.pk}"


class TournamentParticipant(models.Model):
    """Участник турнира с номером посева — раздел «таблица посева»."""

    tournament = models.ForeignKey(
        Tournament, verbose_name="турнир", related_name="participants", on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="участник",
        related_name="tournament_participations", on_delete=models.CASCADE,
    )
    seed = models.PositiveIntegerField("номер посева")

    class Meta:
        verbose_name = "участник турнира"
        verbose_name_plural = "участники турнира"
        ordering = ["seed"]
        unique_together = [("tournament", "user"), ("tournament", "seed")]

    def __str__(self):
        return f"#{self.seed} {self.user}"


class TournamentMatch(models.Model):
    """Ячейка турнирной сетки — раздел «сетка/таблица посева».

    bracket=upper: обычная сетка на выбывание (единственная ветка для
    single-elimination). round_number/position — 0-индексированная позиция
    внутри (bracket, round): матчи (2k, 2k+1) раунда r кормят матч k
    раунда r+1 (чётный -> слот 1, нечётный -> слот 2). Бай возможен только
    в 1-м раунде верхней сетки — так генерируется сетка при непарном числе
    участников.

    bracket=lower: нижняя сетка double-elimination — раунд 1 сводит между
    собой проигравших 1-го раунда верхней сетки; далее раунды чередуются:
    нечётный (>1) раунд — «сокращающий» (сводит выживших нижней сетки между
    собой, вдвое), чётный раунд — «сливающий» (сводит выживших нижней сетки
    с очередной порцией проигравших верхней сетки, без сокращения счёта).

    bracket=final: единственный решающий матч — победитель верхней сетки
    против победителя нижней, за 1-2 место, без bracket reset.
    """

    class Bracket(models.TextChoices):
        UPPER = "upper", "Верхняя сетка"
        LOWER = "lower", "Нижняя сетка"
        FINAL = "final", "Финал"

    tournament = models.ForeignKey(
        Tournament, verbose_name="турнир", related_name="matches", on_delete=models.CASCADE,
    )
    bracket = models.CharField(
        "сетка", max_length=10, choices=Bracket.choices, default=Bracket.UPPER,
    )
    round_number = models.PositiveIntegerField("раунд")
    position = models.PositiveIntegerField("позиция в раунде")

    participant1 = models.ForeignKey(
        TournamentParticipant, verbose_name="участник 1",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )
    participant2 = models.ForeignKey(
        TournamentParticipant, verbose_name="участник 2",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )
    battle = models.OneToOneField(
        "battles.Battle", verbose_name="бой",
        related_name="tournament_match", blank=True, null=True, on_delete=models.SET_NULL,
    )
    winner = models.ForeignKey(
        TournamentParticipant, verbose_name="победитель матча",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "матч сетки"
        verbose_name_plural = "матчи сетки"
        ordering = ["bracket", "round_number", "position"]
        unique_together = [("tournament", "bracket", "round_number", "position")]

    def __str__(self):
        return f"{self.tournament} [{self.bracket}] R{self.round_number}#{self.position}"

    def save(self, *args, **kwargs):
        if self.battle_id and self.battle.winner_id:
            if self.participant1_id and self.battle.winner_id == self.participant1.user_id:
                self.winner = self.participant1
            elif self.participant2_id and self.battle.winner_id == self.participant2.user_id:
                self.winner = self.participant2

        super().save(*args, **kwargs)

        if self.winner_id:
            self._advance()

    def _loser(self):
        if not self.winner_id:
            return None
        if self.participant1_id and self.winner_id == self.participant1_id:
            return self.participant2
        if self.participant2_id and self.winner_id == self.participant2_id:
            return self.participant1
        return None

    def _set_final_result(self):
        loser = self._loser()
        Tournament.objects.filter(pk=self.tournament_id).update(
            winner_id=self.winner.user_id,
            runner_up_id=loser.user_id if loser else None,
        )

    def _advance(self):
        if self.bracket == self.Bracket.FINAL:
            self._set_final_result()
        elif self.bracket == self.Bracket.UPPER:
            self._advance_upper()
        elif self.bracket == self.Bracket.LOWER:
            self._advance_lower()

    def _advance_upper(self):
        next_match = TournamentMatch.objects.filter(
            tournament_id=self.tournament_id, bracket=self.Bracket.UPPER,
            round_number=self.round_number + 1, position=self.position // 2,
        ).first()
        slot = "participant1" if self.position % 2 == 0 else "participant2"

        if next_match is not None:
            if getattr(next_match, f"{slot}_id") != self.winner_id:
                setattr(next_match, slot, self.winner)
                next_match.save()
        elif self.tournament.bracket_type == Tournament.BracketType.SINGLE:
            self._set_final_result()
        else:
            final_match = TournamentMatch.objects.filter(
                tournament_id=self.tournament_id, bracket=self.Bracket.FINAL,
            ).first()
            if final_match is not None and final_match.participant1_id != self.winner_id:
                final_match.participant1 = self.winner
                final_match.save()

        if self.tournament.bracket_type == Tournament.BracketType.DOUBLE:
            loser = self._loser()
            if loser is not None:
                self._drop_to_lower(loser)

    def _drop_to_lower(self, loser):
        """Проигравший верхней сетки падает в соответствующую ячейку нижней.

        Для 1-го раунда верхней сетки дополнительно проверяем, не бай ли
        сосед по паре (тогда второй участник у этой ячейки нижней сетки
        никогда не появится) — в этом случае сразу засчитываем победу.
        """
        if self.round_number == 1:
            lb_round = 1
            lb_position = self.position // 2
            slot = "participant1" if self.position % 2 == 0 else "participant2"
        else:
            lb_round = 2 * (self.round_number - 1)
            lb_position = self.position
            slot = "participant2"

        lb_match = TournamentMatch.objects.filter(
            tournament_id=self.tournament_id, bracket=self.Bracket.LOWER,
            round_number=lb_round, position=lb_position,
        ).first()
        if lb_match is None or getattr(lb_match, f"{slot}_id") == loser.id:
            return

        setattr(lb_match, slot, loser)

        if self.round_number == 1 and not lb_match.winner_id:
            sibling_position = self.position + 1 if self.position % 2 == 0 else self.position - 1
            sibling = TournamentMatch.objects.filter(
                tournament_id=self.tournament_id, bracket=self.Bracket.UPPER,
                round_number=1, position=sibling_position,
            ).first()
            other_slot = "participant2" if slot == "participant1" else "participant1"
            if (
                sibling is not None and sibling.participant2_id is None
                and getattr(lb_match, f"{other_slot}_id") is None
            ):
                lb_match.winner = loser

        lb_match.save()

    def _advance_lower(self):
        total_lb_rounds = self.tournament.lower_bracket_rounds()
        next_round = self.round_number + 1

        if next_round > total_lb_rounds:
            final_match = TournamentMatch.objects.filter(
                tournament_id=self.tournament_id, bracket=self.Bracket.FINAL,
            ).first()
            if final_match is not None and final_match.participant2_id != self.winner_id:
                final_match.participant2 = self.winner
                final_match.save()
            return

        if next_round % 2 == 1:
            # «сокращающий» раунд — соседние победители сводятся друг с другом
            next_position = self.position // 2
            slot = "participant1" if self.position % 2 == 0 else "participant2"
        else:
            # «сливающий» раунд — прямой перенос позиции, слот 1
            # (слот 2 займёт очередной проигравший верхней сетки)
            next_position = self.position
            slot = "participant1"

        next_match = TournamentMatch.objects.filter(
            tournament_id=self.tournament_id, bracket=self.Bracket.LOWER,
            round_number=next_round, position=next_position,
        ).first()
        if next_match is not None and getattr(next_match, f"{slot}_id") != self.winner_id:
            setattr(next_match, slot, self.winner)
            next_match.save()
