from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet
from django.urls import reverse
from django.utils.text import slugify


class Galerie(models.Model):
    """Galerie thématique principale visible sur homepage"""

    nom = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image_couverture = models.ImageField(upload_to='galeries/couvertures/', blank=True)
    ordre_affichage = models.PositiveIntegerField(default=0)
    est_publique = models.BooleanField(default=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordre_affichage', 'nom']
        verbose_name = 'Galerie'
        verbose_name_plural = 'Galeries'

    def __str__(self) -> str:
        return self.nom

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('galeries:galerie_detail', kwargs={'galerie_slug': self.slug})

    def get_collections_publiques(self) -> QuerySet[Collection]:
        return self.collections.filter(est_publique=True).order_by('ordre_affichage')

    def get_photos_directes_publiques(self) -> QuerySet[Photo]:
        """Photos directement liées à la galerie (sans collection)"""
        return self.photos.filter(collection__isnull=True, est_publique=True).order_by('ordre_affichage')

    def a_des_collections(self) -> bool:
        """Vérifie si la galerie utilise le mode hiérarchique"""
        return self.collections.exists()

    def get_total_photos(self) -> int:
        """Compte total photos (directes + dans collections)"""
        photos_directes = self.photos.filter(collection__isnull=True).count()
        photos_collections = sum(collection.photos.count() for collection in self.collections.all())
        return photos_directes + photos_collections

    def get_photo_couverture(self) -> Photo | None:
        """Retourne la photo de couverture de la galerie"""
        if self.a_des_collections():
            # Mode collections : première photo de la première collection
            premiere_collection = self.get_collections_publiques().first()
            return premiere_collection.get_photo_couverture() if premiere_collection else None
        else:
            # Mode direct : première photo ou photo marquée comme couverture
            return (self.get_photos_directes_publiques().filter(est_couverture=True).first() or
                   self.get_photos_directes_publiques().first())


class Collection(models.Model):
    """Collection d'événement ou projet spécifique"""

    galerie = models.ForeignKey(
        Galerie,
        on_delete=models.CASCADE,
        related_name='collections'
    )
    nom = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)

    # Métadonnées événement
    date_evenement = models.DateField(blank=True, null=True)
    lieu = models.CharField(max_length=200, blank=True)

    # Gestion affichage
    ordre_affichage = models.PositiveIntegerField(default=0)
    est_publique = models.BooleanField(default=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('galerie', 'slug')]
        ordering = ['galerie', 'ordre_affichage', 'nom']
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'

    def __str__(self) -> str:
        return f"{self.galerie.nom} - {self.nom}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('galeries:collection_detail', kwargs={
            'galerie_slug': self.galerie.slug,
            'collection_slug': self.slug
        })

    def get_photo_couverture(self) -> Photo | None:
        return self.photos.filter(est_couverture=True).first() or self.photos.first()

    def get_photos_publiques(self) -> QuerySet[Photo]:
        return self.photos.filter(est_publique=True).order_by('ordre_affichage')


class Photo(models.Model):
    """Photo individuelle dans une galerie (directe ou via collection)"""

    galerie = models.ForeignKey(
        Galerie,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='photos',
        blank=True,
        null=True,
        help_text="Laissez vide pour une photo directe dans la galerie"
    )

    # Métadonnées photo
    titre = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # Métadonnées techniques (extraites EXIF)
    date_prise = models.DateTimeField(blank=True, null=True)
    appareil = models.CharField(max_length=100, blank=True)
    objectif = models.CharField(max_length=100, blank=True)
    ouverture = models.CharField(max_length=10, blank=True)
    vitesse = models.CharField(max_length=20, blank=True)
    iso = models.PositiveIntegerField(blank=True, null=True)

    # Dimensions originales
    largeur_originale = models.PositiveIntegerField()
    hauteur_originale = models.PositiveIntegerField()

    # Gestion affichage
    ordre_affichage = models.PositiveIntegerField(default=0)
    est_publique = models.BooleanField(default=True)
    est_couverture = models.BooleanField(default=False)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordre_affichage', 'titre']
        verbose_name = 'Photo'
        verbose_name_plural = 'Photos'

    def __str__(self) -> str:
        return self.titre or f"Photo {self.id}"

    def get_absolute_url(self) -> str:
        return reverse('galeries:photo_detail', kwargs={'photo_id': self.id})

    def est_dans_collection(self) -> bool:
        """Vérifie si la photo est dans une collection ou directe"""
        return self.collection is not None

    def get_conteneur_parent(self) -> Galerie | Collection:
        """Retourne la collection ou la galerie parente selon l'organisation"""
        return self.collection if self.collection else self.galerie

    def get_version_par_defaut(self) -> PhotoVersion | None:
        return self.versions.filter(est_par_defaut=True).first()

    def get_versions_publiques(self) -> QuerySet[PhotoVersion]:
        return self.versions.filter(est_publique=True)


class PhotoVersion(models.Model):
    """Version traitée d'une photo (couleur, monochrome, etc.)"""

    TRAITEMENT_CHOICES = [
        ('couleur', 'Couleur'),
        ('monochrome', 'Monochrome'),
        ('sepia', 'Sépia'),
        ('vintage', 'Vintage'),
    ]

    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    traitement = models.CharField(max_length=20, choices=TRAITEMENT_CHOICES)

    # Fichiers
    fichier_web = models.ImageField(upload_to='photos/web/')  # Optimisé web
    fichier_pleine_resolution = models.ImageField(upload_to='photos/hd/', blank=True)

    # Dimensions version
    largeur = models.PositiveIntegerField()
    hauteur = models.PositiveIntegerField()

    # Gestion
    est_par_defaut = models.BooleanField(default=False)
    est_publique = models.BooleanField(default=True)
    traite_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('photo', 'traitement')]
        verbose_name = 'Version de photo'
        verbose_name_plural = 'Versions de photos'

    def __str__(self) -> str:
        return f"{self.photo.titre or 'Photo'} - {self.get_traitement_display()}"

    def get_url_affichage(self) -> str:
        return self.fichier_web.url

    def get_url_telechargement(self) -> str:
        return self.fichier_pleine_resolution.url if self.fichier_pleine_resolution else self.fichier_web.url
