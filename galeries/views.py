from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Collection, Galerie, Photo


def galerie_detail(request: HttpRequest, galerie_slug: str) -> HttpResponse:
    """Vue galerie - affiche collections OU photos directes selon l'organisation"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=True)

    context: dict[str, Any] = {'galerie': galerie}

    if galerie.a_des_collections():
        # Mode hiérarchique : afficher les collections
        context['collections'] = galerie.get_collections_publiques()
    
    # Toujours inclure les photos directes s'il y en a
    photos_directes = galerie.get_photos_directes_publiques()
    if photos_directes.exists():
        context['photos'] = photos_directes

    return render(request, 'galeries/galerie_detail.html', context)

def collection_detail(request: HttpRequest, galerie_slug: str, collection_slug: str) -> HttpResponse:
    """Vue collection - affiche les photos d'une collection spécifique"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=True)
    collection = get_object_or_404(
        Collection,
        galerie=galerie,
        slug=collection_slug,
        est_publique=True
    )

    photos = collection.get_photos_publiques()

    # Collections précédente et suivante dans la même galerie
    collections_galerie = galerie.collections.filter(est_publique=True).order_by('ordre_affichage', 'cree_le')
    collection_list = list(collections_galerie)

    prev_collection = None
    next_collection = None

    try:
        current_index = collection_list.index(collection)
        if current_index > 0:
            prev_collection = collection_list[current_index - 1]
        if current_index < len(collection_list) - 1:
            next_collection = collection_list[current_index + 1]
    except ValueError:
        pass

    context = {
        'galerie': galerie,
        'collection': collection,
        'photos': photos,
        'prev_collection': prev_collection,
        'next_collection': next_collection,
    }

    return render(request, 'galeries/collection_detail.html', context)


def photo_detail(request: HttpRequest, photo_id: int) -> HttpResponse:
    """Vue photo individuelle avec ses versions"""
    photo = get_object_or_404(Photo, id=photo_id, est_publique=True)

    # Vérifier que la galerie et collection (si applicable) sont publiques
    if not photo.galerie.est_publique:
        raise Http404("Galerie non publique")

    if photo.collection and not photo.collection.est_publique:
        raise Http404("Collection non publique")

    versions = photo.get_versions_publiques()
    version_defaut = photo.get_version_par_defaut()

    context = {
        'photo': photo,
        'galerie': photo.galerie,
        'collection': photo.collection,
        'versions': versions,
        'version_defaut': version_defaut,
    }

    return render(request, 'galeries/photo_detail.html', context)
