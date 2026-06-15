"""
Context processors pour l'app galeries
"""

from .models import ConfigurationSite


def site_config(request):
    """
    Ajoute la configuration du site dans le contexte de tous les templates
    """
    return {"config": ConfigurationSite.get_instance()}
