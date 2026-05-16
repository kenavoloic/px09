from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from django.db import models
from django.urls import reverse
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models import QuerySet


class Client(models.Model):
    """Client du photographe"""
    
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    entreprise = models.CharField(max_length=200, blank=True)
    adresse = models.TextField(blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Notes internes du photographe"
    )
    
    # Métadonnées
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self) -> str:
        if self.entreprise:
            return f"{self.nom} {self.prenom} ({self.entreprise})"
        return f"{self.nom} {self.prenom}"
    
    def get_nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"


class Commande(models.Model):
    """Commande contenant des photos pour un client"""
    
    STATUS_CHOICES = [
        ('en_preparation', 'En préparation'),
        ('livree', 'Livrée'),
        ('expiree', 'Expirée'),
    ]
    
    # Relations
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='commandes'
    )
    
    # Identification
    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Référence unique de la commande (ex: CMD-2024-001)"
    )
    titre = models.CharField(
        max_length=200,
        help_text="Titre de la commande (ex: Mariage Sarah & Thomas)"
    )
    description = models.TextField(blank=True)
    message_client = models.TextField(
        blank=True,
        help_text="Message personnalisé pour le client"
    )
    
    # Gestion d'accès
    code_acces = models.CharField(
        max_length=32,
        unique=True,
        help_text="Code d'accès généré automatiquement"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en_preparation'
    )
    expire_le = models.DateTimeField(
        help_text="Date d'expiration de l'accès client"
    )
    
    # Paramètres de téléchargement
    autoriser_telechargement_web = models.BooleanField(
        default=True,
        help_text="Permettre le téléchargement des versions web"
    )
    autoriser_telechargement_hd = models.BooleanField(
        default=False,
        help_text="Permettre le téléchargement haute résolution"
    )
    
    # Statistiques
    nombre_vues = models.PositiveIntegerField(default=0)
    premiere_visite_le = models.DateTimeField(null=True, blank=True)
    derniere_visite_le = models.DateTimeField(null=True, blank=True)
    nombre_telechargements = models.PositiveIntegerField(default=0)
    
    # Métadonnées
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-cree_le']
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
    
    def __str__(self) -> str:
        return f"{self.reference} - {self.titre}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        # Générer un code d'accès unique si pas encore défini
        if not self.code_acces:
            self.code_acces = self.generer_code_acces()
        
        # Générer une référence si pas encore définie
        if not self.reference:
            self.reference = self.generer_reference()
        
        super().save(*args, **kwargs)
    
    def generer_code_acces(self) -> str:
        """Génère un code d'accès unique"""
        while True:
            code = secrets.token_urlsafe(24)
            if not Commande.objects.filter(code_acces=code).exists():
                return code
    
    def generer_reference(self) -> str:
        """Génère une référence unique avec gestion des conflits"""
        maintenant = timezone.now()
        date_str = maintenant.strftime("%Y_%m_%d")
        
        # Retry jusqu'à trouver un numéro libre (0001 à 9999)
        for tentative in range(1, 10000):
            reference = f"{date_str}_{tentative:04d}"
            if not Commande.objects.filter(reference=reference).exists():
                return reference
        
        # Fallback avec timestamp si plus de 9999 commandes dans la journée
        timestamp = int(maintenant.timestamp())
        return f"{date_str}_{timestamp}"
    
    def est_accessible(self) -> bool:
        """Vérifie si la commande est accessible (non expirée et livrée)"""
        return (
            self.statut == 'livree' and
            self.expire_le > timezone.now()
        )
    
    def est_expiree(self) -> bool:
        """Vérifie si la commande est expirée"""
        return self.expire_le <= timezone.now()
    
    def get_absolute_url(self) -> str:
        """URL d'accès client avec le code"""
        return reverse('commandes:acces_commande', kwargs={
            'code_acces': self.code_acces
        })
    
    def get_admin_url(self) -> str:
        """URL d'administration de la commande"""
        return reverse('admin:commandes_commande_change', args=[self.pk])
    
    def enregistrer_visite(self) -> None:
        """Enregistre une visite client"""
        maintenant = timezone.now()
        self.nombre_vues += 1
        self.derniere_visite_le = maintenant
        
        if not self.premiere_visite_le:
            self.premiere_visite_le = maintenant
        
        self.save(update_fields=[
            'nombre_vues', 'premiere_visite_le', 'derniere_visite_le'
        ])
    
    def enregistrer_telechargement(self) -> None:
        """Enregistre un téléchargement"""
        self.nombre_telechargements += 1
        self.save(update_fields=['nombre_telechargements'])
    
    def get_photos_count(self) -> int:
        """Retourne le nombre de photos dans la commande"""
        return self.photos.count()


class PhotoCommande(models.Model):
    """Photo incluse dans une commande client"""
    
    # Relations
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    photo_originale = models.ForeignKey(
        'galeries.Photo',
        on_delete=models.CASCADE,
        help_text="Photo du portfolio à inclure dans la commande"
    )
    version_selectionnee = models.ForeignKey(
        'galeries.PhotoVersion',
        on_delete=models.CASCADE,
        help_text="Version spécifique à livrer (couleur, monochrome, etc.)"
    )
    
    # Personnalisation pour le client
    titre_personnalise = models.CharField(
        max_length=200,
        blank=True,
        help_text="Titre spécifique pour cette commande (optionnel)"
    )
    commentaire_interne = models.TextField(
        blank=True,
        help_text="Commentaire interne du photographe"
    )
    
    # Gestion d'affichage
    ordre_affichage = models.PositiveIntegerField(default=0)
    
    # Métadonnées
    ajoutee_le = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [('commande', 'photo_originale', 'version_selectionnee')]
        ordering = ['ordre_affichage', 'ajoutee_le']
        verbose_name = 'Photo de commande'
        verbose_name_plural = 'Photos de commande'
    
    def __str__(self) -> str:
        if self.titre_personnalise:
            return f"{self.commande.reference} - {self.titre_personnalise}"
        return f"{self.commande.reference} - {self.photo_originale.get_titre_affichage()}"
    
    def get_titre_affichage(self) -> str:
        """Retourne le titre à afficher au client"""
        if self.titre_personnalise:
            return self.titre_personnalise
        return self.photo_originale.get_titre_affichage()
    
    def get_url_web(self) -> str:
        """URL de la version web"""
        return self.version_selectionnee.fichier_web.url if self.version_selectionnee.fichier_web else ""
    
    def get_url_hd(self) -> str:
        """URL de la version haute résolution"""
        return self.version_selectionnee.fichier_pleine_resolution.url if self.version_selectionnee.fichier_pleine_resolution else ""
    
    def peut_telecharger_hd(self) -> bool:
        """Vérifie si le téléchargement HD est autorisé et disponible"""
        return (
            self.commande.autoriser_telechargement_hd and
            self.version_selectionnee.fichier_pleine_resolution
        )