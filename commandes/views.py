import os
import zipfile
from io import BytesIO

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Commande, PhotoCommande


def acces_commande(request: HttpRequest, code_acces: str) -> HttpResponse:
    """Page d'accès à une commande avec code d'accès"""
    try:
        commande = get_object_or_404(Commande, code_acces=code_acces)

        # Vérifier si la commande est accessible
        if not commande.est_accessible():
            if commande.est_expiree():
                return render(request, 'commandes/commande_expiree.html', {
                    'commande': commande
                })
            else:
                return render(request, 'commandes/commande_non_disponible.html', {
                    'commande': commande
                })

        # Enregistrer la visite
        commande.enregistrer_visite()

        # Récupérer les photos de la commande
        photos = commande.photos.select_related(
            'photo_originale', 'version_selectionnee'
        ).order_by('ordre_affichage')

        context = {
            'commande': commande,
            'photos': photos,
            'peut_telecharger_web': commande.autoriser_telechargement_web,
            'peut_telecharger_hd': commande.autoriser_telechargement_hd,
            'temps_restant': (commande.expire_le - timezone.now()).days if not commande.est_expiree() else 0,
        }

        return render(request, 'commandes/galerie_commande.html', context)

    except Commande.DoesNotExist:
        raise Http404("Code d'accès invalide")


def photo_detail_commande(request: HttpRequest, code_acces: str, photo_id: int) -> HttpResponse:
    """Vue détaillée d'une photo dans une commande"""
    commande = get_object_or_404(Commande, code_acces=code_acces)

    if not commande.est_accessible():
        raise PermissionDenied("Commande non accessible")

    photo_commande = get_object_or_404(
        PhotoCommande,
        commande=commande,
        id=photo_id
    )

    # Récupérer les photos de la commande pour la navigation
    photos = commande.photos.select_related(
        'photo_originale', 'version_selectionnee'
    ).order_by('ordre_affichage')

    # Trouver l'index de la photo actuelle
    photo_index = 0
    photo_precedente = None
    photo_suivante = None

    photos_list = list(photos)
    for i, p in enumerate(photos_list):
        if p.id == photo_commande.id:
            photo_index = i
            if i > 0:
                photo_precedente = photos_list[i-1]
            if i < len(photos_list) - 1:
                photo_suivante = photos_list[i+1]
            break

    context = {
        'commande': commande,
        'photo': photo_commande,
        'photo_precedente': photo_precedente,
        'photo_suivante': photo_suivante,
        'photo_index': photo_index + 1,
        'total_photos': len(photos_list),
        'peut_telecharger_web': commande.autoriser_telechargement_web,
        'peut_telecharger_hd': commande.autoriser_telechargement_hd,
    }

    return render(request, 'commandes/photo_detail_commande.html', context)


@require_POST
def telecharger_photo(request: HttpRequest, code_acces: str, photo_id: int) -> HttpResponse:
    """Téléchargement d'une photo individuelle"""
    commande = get_object_or_404(Commande, code_acces=code_acces)

    if not commande.est_accessible():
        raise PermissionDenied("Commande non accessible")

    photo_commande = get_object_or_404(
        PhotoCommande,
        commande=commande,
        id=photo_id
    )

    # Déterminer le type de téléchargement
    type_telechargement = request.POST.get('type', 'web')

    if type_telechargement == 'hd':
        if not commande.autoriser_telechargement_hd:
            raise PermissionDenied("Téléchargement HD non autorisé")

        if not photo_commande.version_selectionnee.fichier_pleine_resolution:
            messages.error(request, "Version haute résolution non disponible")
            return redirect('commandes:acces_commande', code_acces=code_acces)

        fichier = photo_commande.version_selectionnee.fichier_pleine_resolution
        suffix = '_HD'
    else:
        if not commande.autoriser_telechargement_web:
            raise PermissionDenied("Téléchargement non autorisé")

        fichier = photo_commande.version_selectionnee.fichier_web
        suffix = ''

    if not fichier:
        messages.error(request, "Fichier non disponible")
        return redirect('commandes:acces_commande', code_acces=code_acces)

    # Enregistrer le téléchargement
    commande.enregistrer_telechargement()

    # Préparer le nom de fichier
    nom_original = os.path.splitext(os.path.basename(fichier.name))[0]
    extension = os.path.splitext(fichier.name)[1]
    nom_fichier = f"{commande.reference}_{nom_original}{suffix}{extension}"

    # Réponse de téléchargement
    response = HttpResponse(fichier.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'

    return response


def telecharger_toutes_photos(request: HttpRequest, code_acces: str) -> HttpResponse:
    """Téléchargement de toutes les photos en ZIP"""
    commande = get_object_or_404(Commande, code_acces=code_acces)

    if not commande.est_accessible():
        raise PermissionDenied("Commande non accessible")

    if not commande.autoriser_telechargement_web:
        raise PermissionDenied("Téléchargement non autorisé")

    # Déterminer le type de téléchargement
    type_telechargement = request.GET.get('type', 'web')

    if type_telechargement == 'hd' and not commande.autoriser_telechargement_hd:
        messages.error(request, "Téléchargement HD non autorisé")
        return redirect('commandes:acces_commande', code_acces=code_acces)

    # Créer le fichier ZIP en mémoire
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        photos = commande.photos.select_related(
            'version_selectionnee'
        ).order_by('ordre_affichage')

        for i, photo_commande in enumerate(photos, 1):
            if type_telechargement == 'hd':
                fichier = photo_commande.version_selectionnee.fichier_pleine_resolution
                suffix = '_HD'
            else:
                fichier = photo_commande.version_selectionnee.fichier_web
                suffix = ''

            if fichier:
                try:
                    # Lire le contenu du fichier
                    fichier_content = fichier.read()

                    # Créer le nom de fichier dans le ZIP
                    extension = os.path.splitext(fichier.name)[1]
                    nom_dans_zip = f"{i:03d}_{photo_commande.get_titre_affichage()}{suffix}{extension}"

                    # Nettoyer le nom de fichier (supprimer les caractères problématiques)
                    nom_dans_zip = "".join(c for c in nom_dans_zip if c.isalnum() or c in (' ', '-', '_', '.')).strip()

                    # Ajouter au ZIP
                    zip_file.writestr(nom_dans_zip, fichier_content)

                except Exception as e:
                    # Log l'erreur mais continue avec les autres fichiers
                    print(f"Erreur lors de l'ajout de {fichier.name}: {e}")
                    continue

    # Enregistrer le téléchargement
    commande.enregistrer_telechargement()

    # Préparer la réponse
    zip_buffer.seek(0)

    # Nom du fichier ZIP
    suffix = '_HD' if type_telechargement == 'hd' else ''
    nom_zip = f"{commande.reference}_{commande.titre}{suffix}.zip"
    nom_zip = "".join(c for c in nom_zip if c.isalnum() or c in (' ', '-', '_', '.')).strip()

    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nom_zip}"'

    return response


def aide_commande(request: HttpRequest, code_acces: str) -> HttpResponse:
    """Page d'aide pour les clients"""
    commande = get_object_or_404(Commande, code_acces=code_acces)

    context = {
        'commande': commande,
    }

    return render(request, 'commandes/aide_commande.html', context)
