from typing import Any

from django.core.exceptions import ValidationError
from django.db import models


class AccueilConfig(models.Model):
    """Configuration globale de la page d'accueil - un seul enregistrement"""

    # Informations principales
    titre_site = models.CharField(
        max_length=100, default="HORS LES MURS", help_text="Titre principal du site"
    )
    sous_titre = models.CharField(
        max_length=100,
        default="Studio photographique",
        help_text="Sous-titre affiché sous le titre principal",
    )
    description = models.TextField(
        default="Paysages, architecture, sport, documentaire. Des images capturées hors des sentiers battus, là où la lumière raconte.",
        help_text="Description principale affichée dans la section hero",
    )

    # Image hero
    hero_image = models.ImageField(
        upload_to="accueil/hero/",
        blank=True,
        null=True,
        help_text="Image principale affichée sur la page d'accueil",
    )

    # Textes de sections
    titre_galeries = models.CharField(
        max_length=100, default="Galeries", help_text="Titre de la section galeries"
    )
    titre_acces_prive = models.CharField(
        max_length=100,
        default="Galeries privées",
        help_text="Titre de la section accès privé",
    )
    description_acces_prive = models.TextField(
        default="Vous avez reçu un code d'accès ? Consultez vos photos personnelles en toute confidentialité.",
        help_text="Description de la section accès privé",
    )

    # Textes du modal d'accès privé
    modal_titre = models.CharField(
        max_length=100,
        default="Galerie privée",
        help_text="Titre du modal d'accès privé",
    )
    modal_sous_titre = models.TextField(
        default="Saisissez le code qui vous a été communiqué pour accéder à vos photos.",
        help_text="Sous-titre du modal d'accès privé",
    )
    modal_placeholder_code = models.CharField(
        max_length=50,
        default="ex: HLM-2024-XXX",
        help_text="Placeholder pour le champ code d'accès",
    )

    # Métadonnées
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration de l'accueil"
        verbose_name_plural = "Configuration de l'accueil"

    def __str__(self) -> str:
        return f"Configuration accueil - {self.titre_site}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # S'assurer qu'il n'y a qu'une seule instance
        if not self.pk and AccueilConfig.objects.exists():
            raise ValidationError(
                "Il ne peut y avoir qu'une seule configuration d'accueil"
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls) -> "AccueilConfig":
        """Récupère la configuration d'accueil (crée une instance par défaut si nécessaire)"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class SectionAccueil(models.Model):
    """Sections personnalisables de la page d'accueil"""

    POSITION_CHOICES = [
        ("hero", "Section Hero"),
        ("galeries", "Avant les galeries"),
        ("prive", "Avant accès privé"),
        ("footer", "Avant le footer"),
    ]

    titre = models.CharField(max_length=200)
    contenu = models.TextField(help_text="Contenu de la section (HTML autorisé)")
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        help_text="Position de la section sur la page",
    )
    ordre = models.PositiveIntegerField(
        default=0, help_text="Ordre d'affichage (plus petit en premier)"
    )
    est_active = models.BooleanField(default=True, help_text="Afficher cette section")

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "ordre", "titre"]
        verbose_name = "Section d'accueil"
        verbose_name_plural = "Sections d'accueil"

    def __str__(self) -> str:
        return f"{self.titre} ({self.get_position_display()})"
