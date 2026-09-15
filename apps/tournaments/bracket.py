from .models import Tournament, TournamentMatch


def _standard_seed_order(size):
    """Стандартный порядок посева (1 vs N, 2 vs N-1, ...), чтобы сильные

    сеяные не встречались в первых раундах. Возвращает список номеров
    посева длиной size (степень двойки), в порядке слотов сетки.
    """
    if size == 1:
        return [1]
    prev = _standard_seed_order(size // 2)
    result = []
    for s in prev:
        result.append(s)
        result.append(size + 1 - s)
    return result


def generate_bracket(tournament):
    """Строит сетку на выбывание по текущим участникам турнира.

    Число слотов дополняется до ближайшей степени двойки, лишние слоты —
    баи (без соперника), достаются худшим слотам по порядку посева.
    Для bracket_type=double дополнительно строит нижнюю сетку и финал
    (см. docstring TournamentMatch для описания раундов нижней сетки).
    """
    participants = list(tournament.participants.order_by("seed"))
    n = len(participants)
    if n < 2:
        raise ValueError("Нужно минимум 2 участника.")

    bracket_size = 1
    while bracket_size < n:
        bracket_size *= 2

    seed_order = _standard_seed_order(bracket_size)
    slots = [participants[s - 1] if s <= n else None for s in seed_order]

    total_rounds = bracket_size.bit_length() - 1

    round1_matches = []
    for i in range(0, bracket_size, 2):
        match = TournamentMatch.objects.create(
            tournament=tournament, bracket=TournamentMatch.Bracket.UPPER,
            round_number=1, position=i // 2,
            participant1=slots[i], participant2=slots[i + 1],
        )
        round1_matches.append(match)

    matches_in_round = bracket_size // 2
    for round_number in range(2, total_rounds + 1):
        matches_in_round //= 2
        for position in range(matches_in_round):
            TournamentMatch.objects.create(
                tournament=tournament, bracket=TournamentMatch.Bracket.UPPER,
                round_number=round_number, position=position,
            )

    is_double = tournament.bracket_type == Tournament.BracketType.DOUBLE
    if is_double:
        if total_rounds >= 2:
            _generate_lower_bracket(tournament, total_rounds)
        TournamentMatch.objects.create(
            tournament=tournament, bracket=TournamentMatch.Bracket.FINAL,
            round_number=1, position=0,
        )

    tournament.bracket_generated = True
    tournament.save(update_fields=["bracket_generated"])

    for match in round1_matches:
        _resolve_upper_bye(match)


def _generate_lower_bracket(tournament, total_upper_rounds):
    total_lb_rounds = 2 * (total_upper_rounds - 1)
    upper_round1_matches = tournament.matches.filter(
        bracket=TournamentMatch.Bracket.UPPER, round_number=1,
    ).count()

    match_count = upper_round1_matches // 2
    for lb_round in range(1, total_lb_rounds + 1):
        if lb_round > 1:
            if lb_round % 2 == 1:
                match_count //= 2  # «сокращающий» раунд
            # чётный раунд — «сливающий», число матчей не меняется

        for position in range(match_count):
            TournamentMatch.objects.create(
                tournament=tournament, bracket=TournamentMatch.Bracket.LOWER,
                round_number=lb_round, position=position,
            )


def _resolve_upper_bye(match):
    """Бай возможен только в 1-м раунде верхней сетки — единственный

    участник сразу проходит дальше (и роняет "отсутствующего" проигравшего
    в нижнюю сетку не нужно — см. TournamentMatch._loser()/_advance_upper()).
    """
    if match.winner_id:
        return
    if match.participant1_id and not match.participant2_id:
        match.winner = match.participant1
        match.save()
    elif match.participant2_id and not match.participant1_id:
        match.winner = match.participant2
        match.save()
