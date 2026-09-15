from django.apps import AppConfig


class TournamentsConfig(AppConfig):
    name = "apps.tournaments"
    label = "tournaments"

    def ready(self):
        from . import signals  # noqa: F401
