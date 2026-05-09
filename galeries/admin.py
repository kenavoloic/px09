from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from .apps_proxy import PhotoOrderingProxy, PhotoUploadProxy  # noqa: F401
from .models import Collection, Galerie, Photo, PhotoVersion


class GalerieForm(forms.ModelForm):
    photo_couverture_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(),
        required=False,
        label="Photo de couverture",
        help_text="Sélectionnez une photo existante comme couverture"
    )

    class Meta:
        model = Galerie
        exclude = ['image_couverture']  # On utilise photo_couverture_id à la place

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Populate choices with photos from this gallery
            photos = Photo.objects.filter(galerie=self.instance).select_related('galerie', 'collection').prefetch_related('versions')

            # Create custom labels with photo info
            choices = [('', 'Pas de photo de couverture')]
            for photo in photos:
                collection_info = f" ({photo.collection.nom})" if photo.collection else " (Photo directe)"
                label = f"{photo.titre or f'Photo {photo.id}'}{collection_info}"
                choices.append((str(photo.id), label))

            self.fields['photo_couverture_id'].choices = choices

            # IMPORTANT: Refresh from database to get current state
            self.instance.refresh_from_db()
            photo_couverture = self.instance.get_photo_couverture()
            if photo_couverture:
                self.fields['photo_couverture_id'].initial = str(photo_couverture.id)

    def save(self, commit=True):
        instance = super().save(commit)

        # Store the selected photo ID to handle it later
        selected_photo_id = self.cleaned_data.get('photo_couverture_id')

        def update_photo_cover():
            # Reset all photos in this gallery as non-cover
            Photo.objects.filter(galerie=instance).update(est_couverture=False)

            # Set selected photo as cover if one is selected
            if selected_photo_id:
                try:
                    selected_photo = Photo.objects.get(id=selected_photo_id, galerie=instance)
                    selected_photo.est_couverture = True
                    selected_photo.save()
                except Photo.DoesNotExist:
                    pass

        if commit:
            # If committing now, update immediately
            update_photo_cover()
        else:
            # If not committing yet, store the function to call later
            instance._pending_photo_cover_update = update_photo_cover

        return instance


# Customisation du site admin
admin.site.site_header = "Hors les Murs - Administration"
admin.site.site_title = "Administration Portfolio"


class PhotoVersionInline(admin.TabularInline):
    model = PhotoVersion
    extra = 0
    readonly_fields = ['traite_le']
    fields = ['traitement', 'fichier_web', 'fichier_pleine_resolution', 'largeur', 'hauteur', 'est_par_defaut', 'est_publique']


class PhotoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Photo
    extra = 0
    fields = ['titre', 'ordre_affichage', 'est_publique', 'est_couverture']
    readonly_fields = []

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return super().get_queryset(request).select_related('galerie', 'collection')


class CollectionInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Collection
    extra = 0
    fields = ['nom', 'slug', 'est_publique', 'date_evenement']
    readonly_fields = []


@admin.register(Galerie)
class GalerieAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = GalerieForm
    list_display = ['nom', 'slug', 'est_publique', 'total_collections', 'total_photos', 'modifie_le']
    list_filter = ['est_publique', 'cree_le']
    search_fields = ['nom', 'description']
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [CollectionInline]

    class Media:
        css = {
            'all': ('/static/admin/css/photo_cover_select.css',)
        }
        js = ('/static/admin/js/photo_cover_select.js',)

    fieldsets = (
        (None, {
            'fields': ('nom', 'slug', 'description')
        }),
        ('Affichage', {
            'fields': ('photo_couverture_id', 'ordre_affichage', 'est_publique')
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

    def save_model(self, request, obj, form, change):
        """Override to handle photo cover updates and add success message"""
        super().save_model(request, obj, form, change)

        # Handle pending photo cover update if exists
        if hasattr(obj, '_pending_photo_cover_update'):
            obj._pending_photo_cover_update()
            delattr(obj, '_pending_photo_cover_update')

        if change and hasattr(form, 'cleaned_data'):
            selected_photo_id = form.cleaned_data.get('photo_couverture_id')
            if selected_photo_id:
                try:
                    photo = Photo.objects.get(id=selected_photo_id)
                    self.message_user(request, f"✅ Photo de couverture mise à jour : {photo.titre or f'Photo {photo.id}'}")
                except Photo.DoesNotExist:
                    self.message_user(request, "❌ Photo de couverture introuvable")
            else:
                self.message_user(request, "ℹ️ Aucune photo de couverture sélectionnée")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['actions_rapides'] = [
            {
                'titre': '📷 Upload de photos',
                'url': reverse('galeries_admin:upload_photos'),
                'description': 'Uploader plusieurs photos à la fois'
            },
            {
                'titre': '🔄 Ordre des photos',
                'url': reverse('galeries_admin:photo_ordering'),
                'description': 'Réorganiser l\'ordre d\'affichage'
            }
        ]
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Collection)
class CollectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['nom', 'galerie', 'est_publique', 'total_photos', 'date_evenement']
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
class PhotoAdmin(SortableAdminMixin, admin.ModelAdmin):
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
