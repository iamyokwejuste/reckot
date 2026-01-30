from django.apps import AppConfig


class TicketsConfig(AppConfig):
    name = "apps.tickets"

    def ready(self):
        import apps.tickets.signals  # noqa: F401
