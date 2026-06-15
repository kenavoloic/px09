"""Configuration de l'application d'administration.

Remplace le site d'admin par défaut de Django par CustomAdminSite (dashboard
personnalisé). Comme c'est désormais le site par défaut, django-lucus s'y
applique nativement et les modèles s'y enregistrent via @admin.register.
"""

from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    default_site = "galeries.admin_dashboard.CustomAdminSite"
