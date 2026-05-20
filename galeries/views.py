from typing import Any

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import AccesGalerie, Collection, Galerie, Photo, VisiteurGalerie


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


def galerie_privee(request: HttpRequest, galerie_slug: str) -> HttpResponse:
    """Vue galerie privée - nécessite une authentification"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=False)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect('accueil:index')

    context: dict[str, Any] = {'galerie': galerie, 'est_prive': True}

    if galerie.a_des_collections():
        # Mode hiérarchique : afficher les collections (toutes, même non publiques pour les accès privés)
        context['collections'] = galerie.collections.order_by('ordre_affichage')

    # Photos directes (toutes, même non publiques)
    photos_directes = galerie.photos.filter(collection__isnull=True).order_by('ordre_affichage')
    if photos_directes.exists():
        context['photos'] = photos_directes

    return render(request, 'galeries/galerie_detail.html', context)


def collection_privee(request: HttpRequest, galerie_slug: str, collection_slug: str) -> HttpResponse:
    """Vue collection privée - nécessite une authentification"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=False)
    collection = get_object_or_404(Collection, galerie=galerie, slug=collection_slug)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect('accueil:index')

    # Photos de la collection (toutes, même non publiques)
    photos = collection.photos.order_by('ordre_affichage')

    # Collections précédente et suivante
    collections_galerie = galerie.collections.order_by('ordre_affichage', 'cree_le')
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
        'est_prive': True,
    }

    return render(request, 'galeries/collection_detail.html', context)


def photo_privee(request: HttpRequest, photo_id: int) -> HttpResponse:
    """Vue photo privée - nécessite une authentification"""
    photo = get_object_or_404(Photo, id=photo_id)

    # Vérifier que la photo appartient à une galerie privée
    if photo.galerie.est_publique:
        return redirect('galeries:photo_detail', photo_id=photo_id)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, photo.galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect('accueil:index')

    versions = photo.versions.all()  # Toutes les versions pour les accès privés
    version_defaut = photo.get_version_par_defaut()

    context = {
        'photo': photo,
        'galerie': photo.galerie,
        'collection': photo.collection,
        'versions': versions,
        'version_defaut': version_defaut,
        'est_prive': True,
    }

    return render(request, 'galeries/photo_detail.html', context)


def _verifier_acces_prive(request: HttpRequest, galerie: Galerie) -> bool:
    """Vérifie si l'utilisateur a accès à la galerie privée"""
    token = request.session.get('visiteur_token')
    acces_galerie_id = request.session.get('acces_galerie_id')

    if not token or not acces_galerie_id:
        return False

    try:
        visiteur = VisiteurGalerie.objects.get(token_acces=token)
        acces = AccesGalerie.objects.get(id=acces_galerie_id)

        # Vérifier que l'accès correspond à cette galerie et est valide
        if (acces.galerie == galerie and
            visiteur.acces_galerie == acces and
            visiteur.peut_acceder()):
            return True

    except (VisiteurGalerie.DoesNotExist, AccesGalerie.DoesNotExist):
        pass

    return False


def deconnexion_privee(request: HttpRequest) -> HttpResponse:
    """Déconnexion des galeries privées"""
    # Nettoyer la session
    if 'visiteur_token' in request.session:
        del request.session['visiteur_token']
    if 'acces_galerie_id' in request.session:
        del request.session['acces_galerie_id']

    messages.success(request, "Vous avez été déconnecté des galeries privées.")
    return redirect('accueil:index')


def tableau_bord_prive(request: HttpRequest) -> HttpResponse:
    """Tableau de bord des galeries privées accessibles au visiteur"""
    visiteur_token = request.session.get('visiteur_token')
    if not visiteur_token:
        messages.error(request, "Vous devez vous connecter pour accéder aux galeries privées.")
        return redirect('accueil:index')

    # Récupérer le visiteur
    visiteur = VisiteurGalerie.get_visiteur_par_token(visiteur_token)
    if not visiteur or not visiteur.peut_acceder():
        messages.error(request, "Votre accès n'est plus valide.")
        return redirect('galeries:deconnexion_privee')

    # Récupérer toutes les galeries accessibles à ce visiteur
    galeries_accessibles = VisiteurGalerie.get_galeries_accessibles(visiteur.email)

    # Informations sur le visiteur actuel
    context = {
        'visiteur': visiteur,
        'galeries_accessibles': galeries_accessibles,
        'galerie_courante': visiteur.acces_galerie.galerie,
        'est_prive': True,
    }

    return render(request, 'galeries/tableau_bord_prive.html', context)
