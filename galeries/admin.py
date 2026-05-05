from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Collection, Galerie, Photo, PhotoVersion


class PhotoVersionInline(admin.TabularInline):
    model = PhotoVersion
    extra = 0
    readonly_fields = ['traite_le']
    fields = ['traitement', 'fichier_web', 'fichier_pleine_resolution', 'largeur', 'hauteur', 'est_par_defaut', 'est_publique']


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ['titre', 'ordre_affichage', 'est_publique', 'est_couverture']
    readonly_fields = []

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return super().get_queryset(request).select_related('galerie', 'collection')


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0
    fields = ['nom', 'slug', 'ordre_affichage', 'est_publique', 'date_evenement']
    readonly_fields = []


@admin.register(Galerie)
class GalerieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug', 'est_publique', 'ordre_affichage', 'total_collections', 'total_photos', 'modifie_le']
    list_filter = ['est_publique', 'cree_le']
    search_fields = ['nom', 'description']
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [CollectionInline]

    fieldsets = (
        (None, {
            'fields': ('nom', 'slug', 'description')
        }),
        ('Affichage', {
            'fields': ('image_couverture', 'ordre_affichage', 'est_publique')
        }),
        ('Informations', {
            'fields': ('cree_le', 'modifie_le'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['cree_le', 'modifie_le']

    def total_collections(self, obj: Galerie) -> int:
        return obj.collections.count()
    total_collections.short_description = 'Collections'  # type: ignore[attr-defined]

    def total_photos(self, obj: Galerie) -> int:
        return obj.get_total_photos()
    total_photos.short_description = 'Photos'  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Galerie]:
        return super().get_queryset(request).prefetch_related('collections', 'photos')


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'galerie', 'ordre_affichage', 'est_publique', 'total_photos', 'date_evenement']
    list_filter = ['galerie', 'est_publique', 'date_evenement']
    search_fields = ['nom', 'galerie__nom', 'lieu']
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [PhotoInline]

    fieldsets = (
        (None, {
            'fields': ('galerie', 'nom', 'slug', 'description')
        }),
        ('Événement', {
            'fields': ('date_evenement', 'lieu')
        }),
        ('Affichage', {
            'fields': ('ordre_affichage', 'est_publique')
        }),
        ('Informations', {
            'fields': ('cree_le', 'modifie_le'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['cree_le', 'modifie_le']

    def total_photos(self, obj: Collection) -> int:
        return obj.photos.count()
    total_photos.short_description = 'Photos'  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Collection]:
        return super().get_queryset(request).select_related('galerie').prefetch_related('photos')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['titre_ou_id', 'galerie', 'collection', 'ordre_affichage', 'est_publique', 'est_couverture', 'apercu_photo']
    list_filter = ['galerie', 'collection', 'est_publique', 'est_couverture', 'cree_le']
    search_fields = ['titre', 'galerie__nom', 'collection__nom']
    inlines = [PhotoVersionInline]

    fieldsets = (
        (None, {
            'fields': ('galerie', 'collection', 'titre', 'description')
        }),
        ('Métadonnées techniques', {
            'fields': ('date_prise', 'appareil', 'objectif', 'ouverture', 'vitesse', 'iso', 'largeur_originale', 'hauteur_originale'),
            'classes': ('collapse',)
        }),
        ('Affichage', {
            'fields': ('ordre_affichage', 'est_publique', 'est_couverture')
        }),
        ('Informations', {
            'fields': ('cree_le', 'modifie_le'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['cree_le', 'modifie_le']

    def titre_ou_id(self, obj: Photo) -> str:
        return obj.titre or f"Photo {obj.id}"
    titre_ou_id.short_description = 'Titre'  # type: ignore[attr-defined]

    def apercu_photo(self, obj: Photo) -> str:
        version_defaut = obj.get_version_par_defaut()
        if version_defaut and version_defaut.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" />',
                version_defaut.fichier_web.url
            )
        return "Pas de version"
    apercu_photo.short_description = 'Aperçu'  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return super().get_queryset(request).select_related('galerie', 'collection').prefetch_related('versions')


@admin.register(PhotoVersion)
class PhotoVersionAdmin(admin.ModelAdmin):
    list_display = ['photo_titre', 'traitement', 'largeur', 'hauteur', 'est_par_defaut', 'est_publique', 'apercu']
    list_filter = ['traitement', 'est_par_defaut', 'est_publique', 'traite_le']
    search_fields = ['photo__titre', 'photo__galerie__nom']

    fieldsets = (
        (None, {
            'fields': ('photo', 'traitement')
        }),
        ('Fichiers', {
            'fields': ('fichier_web', 'fichier_pleine_resolution')
        }),
        ('Propriétés', {
            'fields': ('largeur', 'hauteur', 'est_par_defaut', 'est_publique')
        }),
        ('Informations', {
            'fields': ('traite_le',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['traite_le']

    def photo_titre(self, obj: PhotoVersion) -> str:
        return obj.photo.titre or f"Photo {obj.photo.id}"
    photo_titre.short_description = 'Photo'  # type: ignore[attr-defined]

    def apercu(self, obj: PhotoVersion) -> str:
        if obj.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.fichier_web.url
            )
        return "Pas d'image"
    apercu.short_description = 'Aperçu'  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[PhotoVersion]:
        return super().get_queryset(request).select_related('photo__galerie', 'photo__collection')
