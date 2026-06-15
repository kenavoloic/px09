from datetime import timedelta

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html

from .models import Client, Commande, PhotoCommande


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "nom",
        "prenom",
        "email",
        "entreprise",
        "nombre_commandes",
        "derniere_commande",
        "cree_le",
    ]
    list_filter = ["entreprise", "cree_le"]
    search_fields = ["nom", "prenom", "email", "entreprise"]
    readonly_fields = ["cree_le", "modifie_le"]

    fieldsets = (
        (None, {"fields": ("prenom", "nom", "email")}),
        ("Informations de contact", {"fields": ("telephone", "entreprise", "adresse")}),
        ("Notes internes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Métadonnées",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    def nombre_commandes(self, obj: Client) -> int:
        return obj.commandes.count()

    nombre_commandes.short_description = "Commandes"  # type: ignore[attr-defined]

    def derniere_commande(self, obj: Client) -> str:
        derniere = obj.commandes.first()
        if derniere:
            return f"{derniere.reference} ({derniere.cree_le.strftime('%d/%m/%Y')})"
        return "Aucune"

    derniere_commande.short_description = "Dernière commande"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Client]:
        return super().get_queryset(request).prefetch_related("commandes")


class PhotoCommandeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = PhotoCommande
    extra = 0
    fields = [
        "photo_originale",
        "version_selectionnee",
        "titre_personnalise",
        "apercu_photo",
        "ordre_affichage",
    ]
    readonly_fields = ["apercu_photo"]

    def apercu_photo(self, obj):
        if obj and obj.version_selectionnee and obj.version_selectionnee.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.version_selectionnee.fichier_web.url,
            )
        return "Pas d'aperçu"

    apercu_photo.short_description = "Aperçu"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[PhotoCommande]:
        return (
            super()
            .get_queryset(request)
            .select_related("photo_originale", "version_selectionnee", "commande")
        )


class CommandeForm(forms.ModelForm):
    """Formulaire personnalisé pour les commandes"""

    expire_le = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Date et heure d'expiration de l'accès client",
    )

    class Meta:
        model = Commande
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Définir une date d'expiration par défaut à 30 jours
        if not self.instance.pk:  # Nouvelle commande
            default_expiry = timezone.now() + timedelta(days=30)
            self.fields["expire_le"].initial = default_expiry.strftime("%Y-%m-%dT%H:%M")


@admin.register(Commande)
class CommandeAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = CommandeForm
    list_display = [
        "reference",
        "titre",
        "client",
        "statut",
        "nombre_photos",
        "nombre_vues",
        "est_accessible_display",
        "expire_le",
        "cree_le",
        "actions_rapides",
    ]
    list_filter = ["statut", "autoriser_telechargement_hd", "cree_le", "expire_le"]
    search_fields = [
        "reference",
        "titre",
        "client__nom",
        "client__prenom",
        "client__email",
    ]
    readonly_fields = [
        "code_acces",
        "reference",
        "nombre_vues",
        "premiere_visite_le",
        "derniere_visite_le",
        "nombre_telechargements",
        "cree_le",
        "modifie_le",
        "url_acces_client",
    ]
    inlines = [PhotoCommandeInline]

    fieldsets = (
        (None, {"fields": ("client", "reference", "titre", "description")}),
        (
            "Configuration d'accès",
            {"fields": ("statut", "expire_le", "code_acces", "url_acces_client")},
        ),
        (
            "Paramètres de téléchargement",
            {"fields": ("autoriser_telechargement_web", "autoriser_telechargement_hd")},
        ),
        ("Message client", {"fields": ("message_client",), "classes": ("collapse",)}),
        (
            "Statistiques",
            {
                "fields": (
                    "nombre_vues",
                    "premiere_visite_le",
                    "derniere_visite_le",
                    "nombre_telechargements",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Métadonnées",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    def nombre_photos(self, obj: Commande) -> int:
        return obj.get_photos_count()

    nombre_photos.short_description = "Photos"  # type: ignore[attr-defined]

    def est_accessible_display(self, obj: Commande) -> str:
        if obj.est_accessible():
            return format_html('<span style="color: green;">✓ Accessible</span>')
        elif obj.est_expiree():
            return format_html('<span style="color: red;">✗ Expirée</span>')
        else:
            return format_html('<span style="color: orange;">En préparation</span>')

    est_accessible_display.short_description = "Accessibilité"  # type: ignore[attr-defined]

    def url_acces_client(self, obj: Commande) -> str:
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html(
                '<a href="{}" target="_blank">{}</a><br>'
                "<small>Code: <code>{}</code></small>",
                url,
                url,
                obj.code_acces,
            )
        return "Sauvegardez d'abord la commande"

    url_acces_client.short_description = "URL d'accès client"  # type: ignore[attr-defined]

    def actions_rapides(self, obj: Commande) -> str:
        if obj.pk:
            actions = []

            # Action pour marquer comme livrée
            if obj.statut != "livree":
                actions.append(
                    f'<a href="javascript:void(0)" onclick="markAsDelivered({obj.pk})" '
                    f'style="color: green;">📦 Livrer</a>'
                )

            # Action pour prolonger l'accès
            actions.append(
                f'<a href="javascript:void(0)" onclick="extendAccess({obj.pk})" '
                f'style="color: blue;">⏰ Prolonger</a>'
            )

            return format_html(" | ".join(actions))
        return ""

    actions_rapides.short_description = "Actions"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Commande]:
        return (
            super()
            .get_queryset(request)
            .select_related("client")
            .prefetch_related("photos")
        )


@admin.register(PhotoCommande)
class PhotoCommandeAdmin(admin.ModelAdmin):
    list_display = [
        "commande",
        "photo_originale",
        "version_selectionnee",
        "titre_personnalise",
        "apercu_photo",
    ]
    list_filter = ["commande__statut", "version_selectionnee__traitement", "ajoutee_le"]
    search_fields = [
        "commande__reference",
        "commande__titre",
        "photo_originale__titre",
        "titre_personnalise",
    ]
    readonly_fields = ["apercu_photo", "ajoutee_le"]

    def apercu_photo(self, obj):
        if obj.version_selectionnee and obj.version_selectionnee.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: cover; border-radius: 4px;" />',
                obj.version_selectionnee.fichier_web.url,
            )
        return "Pas d'aperçu"

    apercu_photo.short_description = "Aperçu"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[PhotoCommande]:
        return (
            super()
            .get_queryset(request)
            .select_related("commande", "photo_originale", "version_selectionnee")
        )
