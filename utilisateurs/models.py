from typing import Any

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Utilisateur(AbstractUser):
    """Utilisateur étendu avec rôles métier"""

    class Role(models.TextChoices):
        PHOTOGRAPHE = "photographe", "Photographe"
        CLIENT = "client", "Client"
        VISITEUR = "visiteur", "Visiteur"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VISITEUR)
    telephone = models.CharField(max_length=20, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    def est_photographe(self) -> bool:
        return self.role == self.Role.PHOTOGRAPHE

    def est_client(self) -> bool:
        return self.role == self.Role.CLIENT

    def est_visiteur(self) -> bool:
        return self.role == self.Role.VISITEUR

    def clean(self) -> None:
        """Validation métier : un seul photographe autorisé"""
        super().clean()

        if self.role == self.Role.PHOTOGRAPHE:
            # Vérifier qu'il n'y a pas déjà un autre photographe
            photographes_existants = Utilisateur.objects.filter(
                role=self.Role.PHOTOGRAPHE
            ).exclude(pk=self.pk or 0)

            if photographes_existants.exists():
                raise ValidationError(
                    "Un seul photographe est autorisé dans le système. "
                    f"Le photographe actuel est : {getattr(photographes_existants.first(), 'username', 'inconnu')}"
                )

    def save(self, *args: object, **kwargs: Any) -> None:
        """Surcharge pour appeler la validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class ProfilPhotographe(models.Model):
    """Profil spécifique au photographe unique"""

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_photographe"
    )
    nom_entreprise = models.CharField(max_length=200)
    site_web = models.URLField(blank=True)
    biographie = models.TextField(blank=True)
    localisation = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:
        return f"Profil photographe: {self.nom_entreprise}"


class ProfilClient(models.Model):
    """Profil spécifique aux clients"""

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil_client"
    )
    entreprise = models.CharField(max_length=200, blank=True)
    adresse = models.TextField(blank=True)
    notes = models.TextField(blank=True)  # Notes internes du photographe

    def __str__(self) -> str:
        return f"Profil client: {self.utilisateur.get_full_name() or self.utilisateur.username}"
