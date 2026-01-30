from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        import apps.core.signals  # noqa: F401
        import apps.core.image_signals  # noqa: F401
