from django.db import models


class ScheduleEntry(models.Model):
    """Расписание тренировок/занятий клуба — раздел 1 плана.

    Отдельной схемы в разделе 4 плана нет — спроектирована по аналогии с
    уже готовыми моделями. activity — опциональная связь с уже описанным
    справочником разовых активностей (раздел 4.10), чтобы не дублировать
    названия; title — свободное название, если запись не сводится к одной
    из типовых активностей (например, «Общий сбор клуба»).
    """

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Понедельник"
        TUESDAY = 1, "Вторник"
        WEDNESDAY = 2, "Среда"
        THURSDAY = 3, "Четверг"
        FRIDAY = 4, "Пятница"
        SATURDAY = 5, "Суббота"
        SUNDAY = 6, "Воскресенье"

    weekday = models.IntegerField("день недели", choices=Weekday.choices)
    start_time = models.TimeField("начало")
    end_time = models.TimeField("окончание")

    title = models.CharField("название", max_length=200)
    activity = models.ForeignKey(
        "subscriptions.ActivityPrice", verbose_name="активность",
        related_name="schedule_entries", blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Опционально — если занятие соответствует одной из разовых активностей",
    )
    location = models.CharField("место", max_length=200, blank=True)
    notes = models.TextField("заметки", blank=True)
    is_active = models.BooleanField("активно", default=True)

    class Meta:
        verbose_name = "запись расписания"
        verbose_name_plural = "расписание"
        ordering = ["weekday", "start_time"]
        permissions = [
            ("can_manage_schedule", "Может редактировать расписание клуба"),
        ]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%H:%M} — {self.title}"
