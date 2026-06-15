from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.http import HttpRequest
from django.utils.html import format_html

from .models import ProfilClient, ProfilPhotographe, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Administration des utilisateurs avec rôles métier"""

    list_display = [
        "username",
        "email",
        "role",
        "telephone",
        "is_active",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name", "telephone"]

    fieldsets = tuple(
        list(UserAdmin.fieldsets or [])
        + [
            (
                "Informations métier",
                {
                    "fields": ("role", "telephone", "cree_le"),
                },
            ),
        ]
    )

    readonly_fields = ["cree_le"]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Any]:
        return (
            super()
            .get_queryset(request)
            .select_related("profil_photographe", "profil_client")
        )


@admin.register(ProfilPhotographe)
class ProfilPhotographeAdmin(admin.ModelAdmin):
    """Administration du profil photographe"""

    list_display = ["nom_entreprise", "utilisateur", "site_web", "localisation"]
    search_fields = ["nom_entreprise", "utilisateur__username", "localisation"]

    fieldsets = (
        (
            None,
            {
                "fields": ("utilisateur", "nom_entreprise"),
            },
        ),
        (
            "Informations complémentaires",
            {
                "fields": ("site_web", "localisation", "biographie"),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Any]:
        return super().get_queryset(request).select_related("utilisateur")


@admin.register(ProfilClient)
class ProfilClientAdmin(admin.ModelAdmin):
    """Administration des profils clients"""

    list_display = ["utilisateur_nom", "entreprise", "utilisateur_email", "a_des_notes"]
    list_filter = ["utilisateur__date_joined"]
    search_fields = [
        "utilisateur__username",
        "utilisateur__email",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "entreprise",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("utilisateur",),
            },
        ),
        (
            "Informations client",
            {
                "fields": ("entreprise", "adresse"),
            },
        ),
        (
            "Notes internes",
            {
                "fields": ("notes",),
                "description": "Notes privées visibles uniquement par le photographe",
            },
        ),
    )

    def utilisateur_nom(self, obj: ProfilClient) -> str:
        """Nom complet ou nom d'utilisateur"""
        return obj.utilisateur.get_full_name() or obj.utilisateur.username

    utilisateur_nom.short_description = "Nom"  # type: ignore[attr-defined]
    utilisateur_nom.admin_order_field = "utilisateur__first_name"  # type: ignore[attr-defined]

    def utilisateur_email(self, obj: ProfilClient) -> str:
        """Email de l'utilisateur"""
        return obj.utilisateur.email

    utilisateur_email.short_description = "Email"  # type: ignore[attr-defined]
    utilisateur_email.admin_order_field = "utilisateur__email"  # type: ignore[attr-defined]

    def a_des_notes(self, obj: ProfilClient) -> str:
        """Indique si le client a des notes"""
        if obj.notes.strip():
            return format_html('<span style="color: #28a745;">✓ Oui</span>')
        return format_html('<span style="color: #6c757d;">Non</span>')

    a_des_notes.short_description = "Notes"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Any]:
        return super().get_queryset(request).select_related("utilisateur")
