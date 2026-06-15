"""
Middleware pour la gestion de la langue
"""

from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

from galeries.models import ConfigurationSite


class LanguageFromConfigMiddleware(MiddlewareMixin):
    """
    Middleware qui définit la langue active basée sur la configuration du site
    """

    def process_request(self, request):
        """
        Active la langue configurée dans ConfigurationSite
        """
        try:
            config = ConfigurationSite.get_instance()
            if config.langue:
                translation.activate(config.langue)
                request.LANGUAGE_CODE = config.langue
        except Exception:
            # En cas d'erreur (par ex. base de données non initialisée),
            # on garde la langue par défaut
            pass
