from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from .apps_proxy import PhotoOrderingProxy, PhotoUploadProxy  # noqa: F401
from .models import (
    AccesGalerie,
    Collection,
    ConfigurationSite,
    Galerie,
    Photo,
    PhotoVersion,
    VisiteurGalerie,
)


class PhotoSansCollectionFilter(SimpleListFilter):
    """Filtre pour les photos directes (sans collection)"""

    title = "Organisation"
    parameter_name = "dans_collection"

    def lookups(self, request, model_admin):
        return (
            ("sans_collection", "Photos directes (sans collection)"),
            ("avec_collection", "Photos dans des collections"),
        )

    def queryset(self, request, queryset):
        if self.value() == "sans_collection":
            return queryset.filter(collection__isnull=True)
        elif self.value() == "avec_collection":
            return queryset.filter(collection__isnull=False)
        return queryset


class GalerieForm(forms.ModelForm):
    photo_couverture_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(),
        required=False,
        label="Photo de couverture",
        help_text="Sélectionnez une photo existante comme couverture",
    )

    class Meta:
        model = Galerie
        exclude = ["image_couverture"]  # On utilise photo_couverture_id à la place

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Populate choices with photos from this gallery
            photos = (
                Photo.objects.filter(galerie=self.instance)
                .select_related("galerie", "collection")
                .prefetch_related("versions")
            )

            # Create custom labels with photo info
            choices = [("", "Pas de photo de couverture")]
            for photo in photos:
                collection_info = (
                    f" ({photo.collection.nom})"
                    if photo.collection
                    else " (Photo directe)"
                )
                label = f"{photo.get_titre_affichage() or f'Photo {photo.id}'}{collection_info}"
                choices.append((str(photo.id), label))

            self.fields["photo_couverture_id"].choices = choices

            # IMPORTANT: Refresh from database to get current state
            self.instance.refresh_from_db()
            photo_couverture = self.instance.get_photo_couverture()
            if photo_couverture:
                self.fields["photo_couverture_id"].initial = str(photo_couverture.id)

    def save(self, commit=True):
        instance = super().save(commit)

        # Store the selected photo ID to handle it later
        selected_photo_id = self.cleaned_data.get("photo_couverture_id")

        def update_photo_cover():
            # Reset all photos in this gallery as non-cover
            Photo.objects.filter(galerie=instance).update(est_couverture=False)

            # Set selected photo as cover if one is selected
            if selected_photo_id:
                try:
                    selected_photo = Photo.objects.get(
                        id=selected_photo_id, galerie=instance
                    )
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
    readonly_fields = ["traite_le", "taille_fichiers"]
    fields = [
        "traitement",
        "fichier_web",
        "fichier_pleine_resolution",
        "largeur",
        "hauteur",
        "taille_fichiers",
        "est_par_defaut",
        "est_publique",
    ]

    def taille_fichiers(self, obj):
        if obj and obj.pk:
            return obj.get_taille_totale_formatee()
        return "Non calculé"

    taille_fichiers.short_description = "Taille"  # type: ignore[attr-defined]


class PhotoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Photo
    extra = 0
    fields = ["vignette", "titre", "ordre_affichage", "est_publique", "est_couverture"]
    readonly_fields = ["vignette"]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return (
            super()
            .get_queryset(request)
            .select_related("galerie", "collection")
            .prefetch_related("versions")
        )

    def vignette(self, obj):
        """Affiche une vignette de la photo"""
        if obj and obj.pk:
            version_defaut = obj.get_version_par_defaut()
            if version_defaut and version_defaut.fichier_web:
                return format_html(
                    '<img src="{}" alt="{}" style="max-width: 80px; max-height: 60px; object-fit: cover; border-radius: 4px;" />',
                    version_defaut.fichier_web.url,
                    obj.get_titre_affichage() or "Photo",
                )
        return format_html(
            '<div style="width: 80px; height: 60px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666;">📷</div>'
        )

    vignette.short_description = "Aperçu"  # type: ignore[attr-defined]


class CollectionForm(forms.ModelForm):
    """Formulaire personnalisé pour Collection"""

    class Meta:
        model = Collection
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le widget par défaut ModelChoiceField gère automatiquement les choix

    def clean_galerie(self):
        galerie_value = self.cleaned_data.get("galerie")

        # Toujours convertir en instance, même si c'est déjà une instance
        if galerie_value:
            if isinstance(galerie_value, str) and galerie_value.isdigit():
                try:
                    return Galerie.objects.get(pk=int(galerie_value))
                except Galerie.DoesNotExist as e:
                    raise forms.ValidationError("Galerie introuvable") from e
            elif isinstance(galerie_value, int):
                try:
                    return Galerie.objects.get(pk=galerie_value)
                except Galerie.DoesNotExist as e:
                    raise forms.ValidationError("Galerie introuvable") from e
        return galerie_value

    def save(self, commit=True):
        instance = super().save(commit=False)

        # S'assurer que galerie est une instance avant la sauvegarde
        if hasattr(instance, "galerie") and isinstance(instance.galerie, (str, int)):
            try:
                instance.galerie = Galerie.objects.get(pk=int(instance.galerie))
            except (ValueError, Galerie.DoesNotExist):
                pass

        if commit:
            instance.save()
        return instance


class PhotoCollectionForm(forms.ModelForm):
    """Formulaire pour les photos dans une collection"""

    class Meta:
        model = Photo
        fields = ["titre", "ordre_affichage", "est_publique", "est_couverture"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        # La galerie sera définie par l'inline parent
        if commit:
            instance.save()
        return instance


class PhotoCollectionInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline pour les photos dans une collection - gère automatiquement la relation galerie"""

    model = Photo
    form = PhotoCollectionForm
    extra = 0
    fields = ["vignette", "titre", "ordre_affichage", "est_publique", "est_couverture"]
    readonly_fields = ["vignette"]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return (
            super()
            .get_queryset(request)
            .select_related("galerie", "collection")
            .prefetch_related("versions")
        )

    def vignette(self, obj):
        """Affiche une vignette de la photo"""
        if obj and obj.pk:
            version_defaut = obj.get_version_par_defaut()
            if version_defaut and version_defaut.fichier_web:
                return format_html(
                    '<img src="{}" alt="{}" style="max-width: 80px; max-height: 60px; object-fit: cover; border-radius: 4px;" />',
                    version_defaut.fichier_web.url,
                    obj.get_titre_affichage() or "Photo",
                )
        return format_html(
            '<div style="width: 80px; height: 60px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666;">📷</div>'
        )

    vignette.short_description = "Aperçu"  # type: ignore[attr-defined]


class CollectionInlineForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["nom", "slug", "est_publique", "date_evenement", "ordre_affichage"]


class CollectionInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Collection
    form = CollectionInlineForm
    extra = 0
    fields = ["nom", "slug", "ordre_manuel", "est_publique", "date_evenement"]
    readonly_fields = []


@admin.register(Galerie)
class GalerieAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = GalerieForm
    list_display = [
        "nom",
        "slug",
        "est_publique",
        "total_collections",
        "total_photos",
        "taille_totale",
        "modifie_le",
    ]
    list_filter = ["est_publique", "cree_le"]
    search_fields = ["nom", "description"]
    prepopulated_fields = {"slug": ("nom",)}
    inlines = [CollectionInline]

    class Media:
        css = {"all": ("/static/admin/css/photo_cover_select.css",)}
        js = ("/static/admin/js/photo_cover_select.js",)

    fieldsets = (
        (None, {"fields": ("nom", "slug", "description")}),
        (
            "Affichage",
            {
                "fields": (
                    "photo_couverture_id",
                    "ordre_affichage",
                    "ordre_manuel",
                    "afficher_details_techniques",
                    "est_publique",
                )
            },
        ),
        (
            "Informations",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["cree_le", "modifie_le"]

    def total_collections(self, obj: Galerie) -> int:
        return obj.collections.count()

    total_collections.short_description = "Collections"  # type: ignore[attr-defined]

    def total_photos(self, obj: Galerie) -> int:
        return obj.get_total_photos()

    total_photos.short_description = "Photos"  # type: ignore[attr-defined]

    def taille_totale(self, obj: Galerie) -> str:
        return obj.get_taille_totale_formatee()

    taille_totale.short_description = "Taille totale"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Galerie]:
        return super().get_queryset(request).prefetch_related("collections", "photos")

    def save_model(self, request, obj, form, change):
        """Override to handle photo cover updates and add success message"""
        super().save_model(request, obj, form, change)

        # Handle pending photo cover update if exists
        if hasattr(obj, "_pending_photo_cover_update"):
            obj._pending_photo_cover_update()
            delattr(obj, "_pending_photo_cover_update")

        if change and hasattr(form, "cleaned_data"):
            selected_photo_id = form.cleaned_data.get("photo_couverture_id")
            if selected_photo_id:
                try:
                    photo = Photo.objects.get(id=selected_photo_id)
                    self.message_user(
                        request,
                        f"✅ Photo de couverture mise à jour : {photo.get_titre_affichage() or f'Photo {photo.id}'}",
                    )
                except Photo.DoesNotExist:
                    self.message_user(request, "❌ Photo de couverture introuvable")
            else:
                self.message_user(request, "ℹ️ Aucune photo de couverture sélectionnée")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["actions_rapides"] = [
            {
                "titre": "📷 Upload de photos",
                "url": reverse("galeries_admin:upload_photos"),
                "description": "Uploader plusieurs photos à la fois",
            },
            {
                "titre": "🔄 Ordre des photos",
                "url": reverse("galeries_admin:photo_ordering"),
                "description": "Réorganiser l'ordre d'affichage",
            },
        ]
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Collection)
class CollectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = CollectionForm
    list_display = [
        "nom",
        "galerie",
        "est_publique",
        "total_photos",
        "taille_totale",
        "date_evenement",
    ]
    list_filter = ["galerie", "est_publique", "date_evenement"]
    search_fields = ["nom", "galerie__nom", "lieu"]
    prepopulated_fields = {"slug": ("nom",)}
    inlines = [PhotoCollectionInline]

    def save_model(self, request, obj, form, change):
        """Override pour gérer les problèmes de ForeignKey avec django-admin-sortable2"""

        # S'assurer que galerie est une instance avant le save de adminsortable2
        if hasattr(obj, "galerie") and isinstance(obj.galerie, (str, int)):
            try:
                obj.galerie = Galerie.objects.get(pk=int(obj.galerie))
            except (ValueError, Galerie.DoesNotExist):
                pass  # Laisser Django gérer l'erreur normalement

        # Appel direct à ModelAdmin.save_model pour éviter le conflit avec adminsortable2
        admin.ModelAdmin.save_model(self, request, obj, form, change)

    def save_formsets(self, request, form, formsets, change):
        """Gérer la sauvegarde des photos avec la bonne galerie"""
        collection_instance = form.instance if change else form.save()

        for formset in formsets:
            if formset.model == Photo:
                # Sauvegarder les photos avec la galerie de la collection
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.collection = collection_instance
                    instance.galerie = collection_instance.galerie
                    instance.save()
                formset.save_m2m()
            else:
                formset.save()

        if not change:
            super().save_formsets(request, form, formsets, change)

    fieldsets = (
        (None, {"fields": ("galerie", "nom", "slug", "description")}),
        ("Événement", {"fields": ("date_evenement", "lieu")}),
        (
            "Affichage",
            {
                "fields": (
                    "ordre_affichage",
                    "ordre_manuel",
                    "afficher_details_techniques",
                    "est_publique",
                )
            },
        ),
        (
            "Informations",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["cree_le", "modifie_le"]

    def total_photos(self, obj: Collection) -> int:
        return obj.photos.count()

    total_photos.short_description = "Photos"  # type: ignore[attr-defined]

    def taille_totale(self, obj: Collection) -> str:
        return obj.get_taille_totale_formatee()

    taille_totale.short_description = "Taille totale"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Collection]:
        return (
            super()
            .get_queryset(request)
            .select_related("galerie")
            .prefetch_related("photos")
        )


@admin.register(Photo)
class PhotoAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = [
        "apercu_photo",
        "titre_ou_id",
        "galerie",
        "collection",
        "est_publique",
        "est_couverture",
        "ordre_affichage",
    ]
    list_filter = [
        "galerie",
        "collection",
        PhotoSansCollectionFilter,
        "est_publique",
        "est_couverture",
        "cree_le",
    ]
    search_fields = ["titre", "nom_fichier", "galerie__nom", "collection__nom"]
    inlines = [PhotoVersionInline]
    list_editable = ["collection", "est_publique"]
    actions = [
        "attribuer_a_collection",
        "retirer_de_collection",
        "dupliquer_vers_racine",
        "retirer_de_racine",
        "supprimer_photos_confirmees",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "galerie",
                    "collection",
                    "nom_fichier",
                    "titre",
                    "description",
                )
            },
        ),
        (
            "Métadonnées techniques",
            {
                "fields": (
                    "date_prise",
                    "appareil",
                    "objectif",
                    "ouverture",
                    "vitesse",
                    "iso",
                    "largeur_originale",
                    "hauteur_originale",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Affichage",
            {"fields": ("ordre_affichage", "est_publique", "est_couverture")},
        ),
        (
            "Informations",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["cree_le", "modifie_le"]

    def titre_ou_id(self, obj: Photo) -> str:
        titre = obj.get_titre_affichage()
        if titre == "Sans titre":
            return f"{titre} ({obj.get_nom_fichier_sans_extension()})"
        return titre

    titre_ou_id.short_description = "Titre"  # type: ignore[attr-defined]

    def apercu_photo(self, obj: Photo) -> str:
        version_defaut = obj.get_version_par_defaut()
        if version_defaut and version_defaut.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" />',
                version_defaut.fichier_web.url,
            )
        return "Pas de version"

    apercu_photo.short_description = "Aperçu"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Photo]:
        return (
            super()
            .get_queryset(request)
            .select_related("galerie", "collection")
            .prefetch_related("versions")
        )

    def attribuer_a_collection(
        self, request: HttpRequest, queryset: models.QuerySet[Photo]
    ) -> None:
        """Action pour attribuer des photos à une collection"""
        # Vérifier que toutes les photos sont de la même galerie
        galeries = set(queryset.values_list("galerie_id", flat=True))
        if len(galeries) > 1:
            self.message_user(
                request,
                "❌ Toutes les photos doivent être de la même galerie",
                level="ERROR",
            )
            return

        if not galeries:
            self.message_user(request, "❌ Aucune photo sélectionnée", level="ERROR")
            return

        galerie_id = galeries.pop()
        from django import forms
        from django.template.response import TemplateResponse

        class CollectionChoiceForm(forms.Form):
            collection = forms.ModelChoiceField(
                queryset=Collection.objects.filter(galerie_id=galerie_id),
                required=False,
                empty_label="Aucune collection (photos directes)",
                help_text="Sélectionnez une collection pour ces photos",
            )

        if request.POST.get("confirm"):
            form = CollectionChoiceForm(request.POST)
            if form.is_valid():
                collection = form.cleaned_data["collection"]
                count = queryset.update(collection=collection)
                if collection:
                    self.message_user(
                        request,
                        f"✅ {count} photo(s) attribuée(s) à la collection '{collection.nom}'",
                    )
                else:
                    self.message_user(
                        request, f"✅ {count} photo(s) retirée(s) de leur collection"
                    )
                return None
        else:
            form = CollectionChoiceForm()

        context = {
            "form": form,
            "photos": queryset,
            "action_name": "attribuer_a_collection",
            "title": f"Attribuer {queryset.count()} photo(s) à une collection",
        }

        return TemplateResponse(
            request, "admin/galeries/attribuer_collection.html", context
        )

    attribuer_a_collection.short_description = "🗂️ Attribuer à une collection"  # type: ignore[attr-defined]

    def retirer_de_collection(
        self, request: HttpRequest, queryset: models.QuerySet[Photo]
    ) -> None:
        """Action pour retirer des photos de leur collection (deviennent photos directes)"""
        photos_dans_collections = queryset.exclude(collection__isnull=True)
        photos_directes = queryset.filter(collection__isnull=True)

        if photos_directes.exists():
            self.message_user(
                request,
                f"ℹ️ {photos_directes.count()} photo(s) étaient déjà des photos directes",
                level="WARNING",
            )

        if photos_dans_collections.exists():
            count = photos_dans_collections.update(collection=None)
            self.message_user(
                request,
                f"✅ {count} photo(s) retirée(s) de leur collection et converties en photos directes",
            )
        else:
            self.message_user(
                request, "ℹ️ Aucune photo dans une collection à retirer", level="WARNING"
            )

    retirer_de_collection.short_description = (
        "↩️ Retirer des collections (photos directes)"  # type: ignore[attr-defined]
    )

    def dupliquer_vers_racine(
        self, request: HttpRequest, queryset: models.QuerySet[Photo]
    ) -> None:
        """Action pour dupliquer des photos de collection vers la racine de galerie"""
        from django.contrib import messages
        from django.core.files.base import ContentFile

        photos_dans_collections = queryset.exclude(collection__isnull=True)
        photos_directes = queryset.filter(collection__isnull=True)

        if photos_directes.exists():
            messages.warning(
                request,
                f"❌ {photos_directes.count()} photo(s) ignorée(s) : déjà à la racine",
            )

        if not photos_dans_collections.exists():
            messages.warning(
                request,
                "ℹ️ Aucune photo dans une collection à dupliquer vers la racine",
            )
            return

        duplicatas_crees = 0
        for photo in photos_dans_collections:
            # Créer une copie de la photo pour la racine
            nouvelle_photo = Photo(
                galerie=photo.galerie,
                collection=None,  # À la racine
                nom_fichier=photo.nom_fichier,
                titre=f"{photo.titre} (racine)" if photo.titre else "",
                description=photo.description,
                date_prise=photo.date_prise,
                appareil=photo.appareil,
                objectif=photo.objectif,
                ouverture=photo.ouverture,
                vitesse=photo.vitesse,
                iso=photo.iso,
                largeur_originale=photo.largeur_originale,
                hauteur_originale=photo.hauteur_originale,
                ordre_affichage=photo.galerie.get_total_photos() + 1,
                est_publique=photo.est_publique,
            )
            nouvelle_photo.save()

            # Dupliquer les versions
            for version in photo.versions.all():
                nouvelle_version = PhotoVersion(
                    photo=nouvelle_photo,
                    traitement=version.traitement,
                    largeur=version.largeur,
                    hauteur=version.hauteur,
                    est_par_defaut=version.est_par_defaut,
                    est_publique=version.est_publique,
                )

                # Copier les fichiers
                if version.fichier_web:
                    with version.fichier_web.open("rb") as f:
                        content = ContentFile(f.read())
                        nouvelle_version.fichier_web.save(
                            f"racine_{version.fichier_web.name}", content, save=False
                        )

                if version.fichier_pleine_resolution:
                    with version.fichier_pleine_resolution.open("rb") as f:
                        content = ContentFile(f.read())
                        nouvelle_version.fichier_pleine_resolution.save(
                            f"racine_{version.fichier_pleine_resolution.name}",
                            content,
                            save=False,
                        )

                nouvelle_version.save()

            duplicatas_crees += 1

        messages.success(
            request,
            f"✅ {duplicatas_crees} photo(s) dupliquée(s) vers la racine de galerie",
        )

    dupliquer_vers_racine.short_description = "📋 Dupliquer vers la racine de galerie"  # type: ignore[attr-defined]

    def retirer_de_racine(
        self, request: HttpRequest, queryset: models.QuerySet[Photo]
    ) -> None:
        """Action pour supprimer les photos directes (racine) en gardant celles en collection"""
        import os

        from django.contrib import messages

        photos_directes = queryset.filter(collection__isnull=True)
        photos_dans_collections = queryset.exclude(collection__isnull=True)

        if photos_dans_collections.exists():
            messages.warning(
                request,
                f"❌ {photos_dans_collections.count()} photo(s) ignorée(s) : dans des collections",
            )

        if not photos_directes.exists():
            messages.warning(
                request,
                "ℹ️ Aucune photo directe (racine) à supprimer",
            )
            return

        photos_supprimees = 0
        for photo in photos_directes:
            # Supprimer les fichiers physiques
            for version in photo.versions.all():
                if version.fichier_web:
                    try:
                        if os.path.exists(version.fichier_web.path):
                            os.remove(version.fichier_web.path)
                    except Exception:
                        pass

                if version.fichier_pleine_resolution:
                    try:
                        if os.path.exists(version.fichier_pleine_resolution.path):
                            os.remove(version.fichier_pleine_resolution.path)
                    except Exception:
                        pass

            # Supprimer la photo de la DB
            photo.delete()
            photos_supprimees += 1

        messages.success(
            request,
            f"✅ {photos_supprimees} photo(s) supprimée(s) de la racine de galerie",
        )

    retirer_de_racine.short_description = (
        "🗑️ Supprimer de la racine (garder collections)"  # type: ignore[attr-defined]
    )

    def supprimer_photos_confirmees(
        self, request: HttpRequest, queryset: models.QuerySet[Photo]
    ) -> None:
        """Action pour supprimer des photos avec confirmation"""
        import os

        from django.template.response import TemplateResponse

        if request.POST.get("confirm_delete"):
            # Suppression confirmée
            photos_supprimees = []
            fichiers_supprimes = []

            for photo in queryset:
                # Collecter infos avant suppression
                photo_info = {
                    "titre": photo.get_titre_affichage() or f"Photo {photo.id}",
                    "galerie": photo.galerie.nom,
                    "collection": photo.collection.nom
                    if photo.collection
                    else "Photo directe",
                }
                photos_supprimees.append(photo_info)

                # Supprimer les fichiers physiques des versions
                for version in photo.versions.all():
                    if version.fichier_web:
                        try:
                            if os.path.exists(version.fichier_web.path):
                                os.remove(version.fichier_web.path)
                                fichiers_supprimes.append(version.fichier_web.name)
                        except Exception:
                            pass  # Ignorer les erreurs de fichier

                    if version.fichier_pleine_resolution:
                        try:
                            if os.path.exists(version.fichier_pleine_resolution.path):
                                os.remove(version.fichier_pleine_resolution.path)
                                fichiers_supprimes.append(
                                    version.fichier_pleine_resolution.name
                                )
                        except Exception:
                            pass

            # Supprimer de la base de données
            count, details = queryset.delete()

            # Messages de retour
            self.message_user(
                request,
                f"✅ {len(photos_supprimees)} photo(s) supprimée(s) avec succès",
            )
            if fichiers_supprimes:
                self.message_user(
                    request,
                    f"🗑️ {len(fichiers_supprimes)} fichier(s) physique(s) supprimé(s)",
                )

            return None

        # Afficher la page de confirmation
        context = {
            "photos": queryset,
            "action_name": "supprimer_photos_confirmees",
            "title": f"Supprimer {queryset.count()} photo(s)",
        }

        return TemplateResponse(
            request, "admin/galeries/confirmer_suppression.html", context
        )

    supprimer_photos_confirmees.short_description = (
        "🗑️ Supprimer les photos sélectionnées"  # type: ignore[attr-defined]
    )


@admin.register(PhotoVersion)
class PhotoVersionAdmin(admin.ModelAdmin):
    list_display = [
        "photo_titre",
        "traitement",
        "largeur",
        "hauteur",
        "est_par_defaut",
        "est_publique",
        "apercu",
    ]
    list_filter = ["traitement", "est_par_defaut", "est_publique", "traite_le"]
    search_fields = ["photo__titre", "photo__galerie__nom"]

    fieldsets = (
        (None, {"fields": ("photo", "traitement")}),
        ("Fichiers", {"fields": ("fichier_web", "fichier_pleine_resolution")}),
        (
            "Propriétés",
            {"fields": ("largeur", "hauteur", "est_par_defaut", "est_publique")},
        ),
        ("Informations", {"fields": ("traite_le",), "classes": ("collapse",)}),
    )

    readonly_fields = ["traite_le"]

    def photo_titre(self, obj: PhotoVersion) -> str:
        return obj.photo.get_titre_affichage() or f"Photo {obj.photo.id}"

    photo_titre.short_description = "Photo"  # type: ignore[attr-defined]

    def apercu(self, obj: PhotoVersion) -> str:
        if obj.fichier_web:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.fichier_web.url,
            )
        return "Pas d'image"

    apercu.short_description = "Aperçu"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[PhotoVersion]:
        return (
            super()
            .get_queryset(request)
            .select_related("photo__galerie", "photo__collection")
        )


@admin.register(ConfigurationSite)
class ConfigurationSiteAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Affichage",
            {
                "fields": ("affichage_titre_vide",),
                "description": "Configuration pour l'affichage des photos sans titre personnalisé.",
            },
        ),
        (
            "Langue",
            {
                "fields": ("langue",),
                "description": "Configuration de la langue par défaut de l'application.",
            },
        ),
    )

    def has_add_permission(self, request):
        # Ne permettre qu'une seule instance
        return not ConfigurationSite.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression
        return False


class VisiteurGalerieInline(admin.TabularInline):
    """Inline pour gérer les visiteurs d'un accès galerie"""

    model = VisiteurGalerie
    extra = 1
    fields = [
        "email",
        "nom",
        "est_actif",
        "date_premier_acces",
        "date_dernier_acces",
        "nombre_visites",
    ]
    readonly_fields = [
        "token_acces",
        "date_premier_acces",
        "date_dernier_acces",
        "nombre_visites",
    ]

    def get_readonly_fields(self, request, obj=None):
        """Rendre certains champs readonly après création"""
        readonly = list(self.readonly_fields)
        if obj:  # Si l'objet existe déjà (modification)
            readonly.extend(["email"])  # L'email ne peut plus être modifié
        return readonly


@admin.register(AccesGalerie)
class AccesGalerieAdmin(admin.ModelAdmin):
    list_display = [
        "galerie",
        "titre_acces_ou_code",
        "code_acces",
        "nombre_visiteurs",
        "nombre_acces",
        "est_actif",
        "date_expiration",
    ]
    list_filter = ["est_actif", "date_expiration", "galerie", "date_creation"]
    search_fields = ["galerie__nom", "titre_acces", "code_acces"]
    inlines = [VisiteurGalerieInline]
    readonly_fields = ["code_acces", "nombre_acces", "date_creation", "modifie_le"]

    fieldsets = (
        (None, {"fields": ("galerie", "titre_acces", "code_acces")}),
        (
            "Configuration d'accès",
            {
                "fields": (
                    "date_expiration",
                    "nombre_max_visiteurs",
                    "permettre_telechargement",
                )
            },
        ),
        ("État", {"fields": ("est_actif", "nombre_acces")}),
        (
            "Informations",
            {"fields": ("date_creation", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    def titre_acces_ou_code(self, obj: AccesGalerie) -> str:
        """Affiche le titre personnalisé ou le code d'accès"""
        return obj.titre_acces or f"Accès {obj.code_acces}"

    titre_acces_ou_code.short_description = "Titre"  # type: ignore[attr-defined]

    def nombre_visiteurs(self, obj: AccesGalerie) -> int:
        """Nombre de visiteurs autorisés"""
        return obj.visiteurs.filter(est_actif=True).count()

    nombre_visiteurs.short_description = "Visiteurs"  # type: ignore[attr-defined]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("galerie")
            .prefetch_related("visiteurs")
        )


@admin.register(VisiteurGalerie)
class VisiteurGalerieAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "nom",
        "galerie_nom",
        "code_acces",
        "est_actif",
        "date_dernier_acces",
        "nombre_visites",
    ]
    list_filter = ["est_actif", "acces_galerie__galerie", "date_dernier_acces"]
    search_fields = [
        "email",
        "nom",
        "acces_galerie__galerie__nom",
        "acces_galerie__code_acces",
    ]
    readonly_fields = [
        "token_acces",
        "date_premier_acces",
        "date_dernier_acces",
        "nombre_visites",
        "cree_le",
        "modifie_le",
    ]

    fieldsets = (
        (None, {"fields": ("acces_galerie", "email", "nom")}),
        ("Authentification", {"fields": ("token_acces",), "classes": ("collapse",)}),
        (
            "Activité",
            {"fields": ("date_premier_acces", "date_dernier_acces", "nombre_visites")},
        ),
        ("État", {"fields": ("est_actif",)}),
        (
            "Informations",
            {"fields": ("cree_le", "modifie_le"), "classes": ("collapse",)},
        ),
    )

    def galerie_nom(self, obj: VisiteurGalerie) -> str:
        """Nom de la galerie"""
        return obj.acces_galerie.galerie.nom

    galerie_nom.short_description = "Galerie"  # type: ignore[attr-defined]

    def code_acces(self, obj: VisiteurGalerie) -> str:
        """Code d'accès"""
        return obj.acces_galerie.code_acces

    code_acces.short_description = "Code"  # type: ignore[attr-defined]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("acces_galerie__galerie")

    def save_model(self, request, obj, form, change):
        """Envoyer un email de notification lors de l'ajout d'un nouveau visiteur"""
        is_new = not change
        super().save_model(request, obj, form, change)

        if is_new:
            try:
                if obj.envoyer_notification_acces():
                    self.message_user(
                        request, f"✅ Email de notification envoyé à {obj.email}"
                    )
                else:
                    self.message_user(
                        request,
                        f"⚠️ Impossible d'envoyer l'email à {obj.email}",
                        level="WARNING",
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Erreur lors de l'envoi de l'email : {e}",
                    level="ERROR",
                )
