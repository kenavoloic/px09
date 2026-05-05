from django.apps import AppConfig


class UtilisateursConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utilisateurs"

    def ready(self) -> None:
        """Importer les signaux quand l'app est prête"""
        import utilisateurs.signals  # noqa: F401
