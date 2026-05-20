from django.apps import AppConfig


class GaleriesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "galeries"

    def ready(self) -> None:
        import galeries.signals  # noqa: F401
