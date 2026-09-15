from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.penalties.models import Penalty


class Command(BaseCommand):
    """Раздел 4.17 плана: авто-сгорание замечаний/предупреждений по expires_at.

    Запускать по расписанию (cron / Windows Task Scheduler), например раз в час:
    python manage.py expire_penalties
    """

    help = "Переводит просроченные активные взыскания в статус 'expired'"

    def handle(self, *args, **options):
        expired = Penalty.objects.filter(
            status=Penalty.Status.ACTIVE,
            expires_at__isnull=False,
            expires_at__lte=timezone.now(),
        )
        count = expired.update(status=Penalty.Status.EXPIRED)
        self.stdout.write(self.style.SUCCESS(f"Сгорело взысканий: {count}"))
