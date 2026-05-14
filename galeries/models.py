from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit

if TYPE_CHECKING:
    from django.db.models import QuerySet
from django.urls import reverse
from django.utils.text import slugify


class ConfigurationSite(models.Model):
    """Configuration globale du site (singleton)"""
    
    AFFICHAGE_TITRE_CHOICES = [
        ('sans_titre', 'Afficher "Sans titre"'),
        ('vide', 'Afficher une chaîne vide'),
    ]
    
    affichage_titre_vide = models.CharField(
        max_length=20,
        choices=AFFICHAGE_TITRE_CHOICES,
        default='sans_titre',
        help_text="Comment afficher les photos sans titre personnalisé",
        verbose_name="Affichage des photos sans titre"
    )
    
    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"
    
    def __str__(self) -> str:
        return "Configuration du site"
    
    @classmethod
    def get_instance(cls) -> 'ConfigurationSite':
        """Récupère l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        # Forcer l'ID à 1 pour maintenir le singleton
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args: Any, **kwargs: Any) -> None:
        # Empêcher la suppression du singleton
        pass


class Galerie(models.Model):
    """Galerie thématique principale visible sur homepage"""

    nom = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image_couverture = models.ImageField(upload_to='galeries/couvertures/', blank=True)
    ordre_affichage = models.PositiveIntegerField(default=0)
    ordre_manuel = models.BooleanField(
        default=True,
        verbose_name="Ordre manuel",
        help_text="Si coché, respecte l'ordre défini par le photographe. Sinon, optimise automatiquement le masonry."
    )
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
        # D'abord chercher une photo explicitement marquée comme couverture
        photo_couverture = self.photos.filter(est_couverture=True, est_publique=True).first()
        if photo_couverture:
            return photo_couverture
            
        # Pas de fallback automatique - retourner None si aucune photo n'est marquée comme couverture
        return None


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
    ordre_manuel = models.BooleanField(
        default=True,
        verbose_name="Ordre manuel",
        help_text="Si coché, respecte l'ordre défini par le photographe. Sinon, optimise automatiquement le masonry."
    )
    est_publique = models.BooleanField(default=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('galerie', 'slug')]
        ordering = ['ordre_affichage', 'nom']
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
    nom_fichier = models.CharField(max_length=255, blank=True, help_text="Nom du fichier original")
    titre = models.CharField(max_length=200, blank=True, help_text="Titre personnalisé (optionnel)")
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
        return self.get_titre_affichage() or f"Photo {self.id}"
    
    def a_titre_personnalise(self) -> bool:
        """Vérifie si la photo a un vrai titre personnalisé (pas juste le nom de fichier)"""
        if not self.titre:
            return False
        
        # Comparer avec le nom de fichier sans extension
        nom_fichier_sans_ext = self.get_nom_fichier_sans_extension()
        # Vérifier si le titre est différent du nom de fichier (avec ou sans espaces/underscores)
        titre_nettoye = self.titre.replace(' ', '_').replace('-', '_').lower()
        nom_nettoye = nom_fichier_sans_ext.replace(' ', '_').replace('-', '_').lower()
        
        return titre_nettoye != nom_nettoye
    
    def get_titre_affichage(self) -> str:
        """Retourne le titre à afficher selon la configuration du site"""
        if self.a_titre_personnalise():
            return self.titre
        
        config = ConfigurationSite.get_instance()
        if config.affichage_titre_vide == 'sans_titre':
            return "Sans titre"
        else:
            return ""
    
    def get_titre_survol(self) -> str:
        """Retourne le titre pour les tooltips au survol (toujours explicite)"""
        if self.a_titre_personnalise():
            return self.titre
        
        config = ConfigurationSite.get_instance()
        if config.affichage_titre_vide == 'sans_titre':
            return "Sans titre"
        else:
            return ""  # Même comportement que get_titre_affichage pour la cohérence
    
    def get_nom_fichier_sans_extension(self) -> str:
        """Retourne le nom de fichier sans l'extension"""
        import os
        return os.path.splitext(self.nom_fichier)[0]

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
    
    def get_appareil_nettoye(self) -> str:
        """Retourne le nom de l'appareil sans doublons de marque"""
        if not self.appareil:
            return ""
        
        # Nettoyer les doublons de marque (ex: "Canon Canon EOS 6D" -> "Canon EOS 6D")
        appareil = self.appareil.strip()
        
        # Liste des marques communes
        marques = ['Canon', 'Nikon', 'Sony', 'Fuji', 'Fujifilm', 'Olympus', 'Pentax', 'Leica', 'Panasonic']
        
        for marque in marques:
            # Si la marque apparaît au début deux fois, supprimer la première occurrence
            double_marque = f"{marque} {marque}"
            if appareil.startswith(double_marque):
                appareil = appareil[len(marque):].strip()
                break
                
        return appareil
    
    def get_ouverture_nettoyee(self) -> str:
        """Retourne l'ouverture sans le "/1" superflu"""
        if not self.ouverture:
            return ""
        
        ouverture = str(self.ouverture).strip()
        
        # Supprimer "/1" à la fin
        if ouverture.endswith('/1'):
            ouverture = ouverture[:-2]
            
        # S'assurer qu'on a le préfixe f/ si c'est juste un nombre
        if ouverture and not ouverture.startswith('f/'):
            ouverture = f"f/{ouverture}"
            
        return ouverture


class PhotoVersion(models.Model):
    """Version traitée d'une photo (couleur, monochrome, etc.)"""

    TRAITEMENT_CHOICES = [
        ('couleur', 'Couleur'),
        ('monochrome', 'Monochrome')
        # ('sepia', 'Sépia'),
        #('vintage', 'Vintage'),
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

    # Tailles de fichiers (en octets)
    taille_fichier_web = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Taille du fichier web en octets"
    )
    taille_fichier_hd = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Taille du fichier haute définition en octets"
    )

    # Gestion
    est_par_defaut = models.BooleanField(default=False)
    est_publique = models.BooleanField(default=True)
    traite_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('photo', 'traitement')]
        verbose_name = 'Version de photo'
        verbose_name_plural = 'Versions de photos'

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Calcule automatiquement la taille des fichiers lors de la sauvegarde"""
        super().save(*args, **kwargs)
        
        # Calculer la taille du fichier web
        if self.fichier_web and hasattr(self.fichier_web, 'path'):
            try:
                self.taille_fichier_web = os.path.getsize(self.fichier_web.path)
            except (OSError, FileNotFoundError):
                self.taille_fichier_web = None
        
        # Calculer la taille du fichier HD
        if self.fichier_pleine_resolution and hasattr(self.fichier_pleine_resolution, 'path'):
            try:
                self.taille_fichier_hd = os.path.getsize(self.fichier_pleine_resolution.path)
            except (OSError, FileNotFoundError):
                self.taille_fichier_hd = None
        
        # Sauvegarder à nouveau si les tailles ont été mises à jour
        if self.taille_fichier_web is not None or self.taille_fichier_hd is not None:
            super().save(update_fields=['taille_fichier_web', 'taille_fichier_hd'])

    def __str__(self) -> str:
        return f"{self.photo.titre or 'Photo'} - {self.get_traitement_display()}"

    def get_url_affichage(self) -> str:
        return self.fichier_web.url

    def get_url_telechargement(self) -> str:
        return self.fichier_pleine_resolution.url if self.fichier_pleine_resolution else self.fichier_web.url
    
    def get_taille_totale(self) -> int:
        """Retourne la taille totale en octets (fichiers web + HD)"""
        total = 0
        if self.taille_fichier_web:
            total += self.taille_fichier_web
        if self.taille_fichier_hd:
            total += self.taille_fichier_hd
        return total
    
    def get_taille_totale_formatee(self) -> str:
        """Retourne la taille totale formatée (ex: '2.5 MB')"""
        return self.format_taille(self.get_taille_totale())
    
    @staticmethod
    def format_taille(taille_octets: int) -> str:
        """Formate une taille en octets vers une chaîne lisible"""
        if taille_octets == 0:
            return "0 B"
        
        unites = ['B', 'KB', 'MB', 'GB']
        taille = float(taille_octets)
        
        for unite in unites:
            if taille < 1024.0:
                return f"{taille:.1f} {unite}"
            taille /= 1024.0
        
        return f"{taille:.1f} TB"
    
    # Génération automatique de versions optimisées
    thumbnail = ImageSpecField(
        source='fichier_web',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )
    
    lightbox = ImageSpecField(
        source='fichier_web',
        processors=[ResizeToFit(2560, 1440)],
        format='JPEG',
        options={'quality': 92}
    )
    
    gallery_preview = ImageSpecField(
        source='fichier_web',
        processors=[ResizeToFit(800, 600)],
        format='JPEG',
        options={'quality': 88}
    )
