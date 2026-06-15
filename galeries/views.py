import os
import tempfile
import zipfile

from django.contrib import messages
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .models import Collection, Galerie, Photo, VisiteurGalerie


def galerie_detail(request, galerie_slug):
    """Vue galerie - affiche collections OU photos directes selon l'organisation"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=True)

    context = {"galerie": galerie}

    if galerie.a_des_collections():
        # Mode hiérarchique : afficher les collections
        context["collections"] = galerie.get_collections_publiques()

    # Toujours inclure les photos directes s'il y en a
    photos_directes = galerie.get_photos_directes_publiques()
    if photos_directes.exists():
        context["photos"] = photos_directes

    return render(request, "galeries/galerie_detail.html", context)


def collection_detail(request, galerie_slug, collection_slug):
    """Vue collection - affiche les photos d'une collection spécifique"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=True)
    collection = get_object_or_404(
        Collection, galerie=galerie, slug=collection_slug, est_publique=True
    )

    photos = collection.get_photos_publiques()

    # Collections précédente et suivante dans la même galerie
    collections_galerie = galerie.collections.filter(est_publique=True).order_by(
        "ordre_affichage", "cree_le"
    )
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
        "galerie": galerie,
        "collection": collection,
        "photos": photos,
        "prev_collection": prev_collection,
        "next_collection": next_collection,
    }

    return render(request, "galeries/collection_detail.html", context)


def photo_detail(request, photo_id):
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
        "photo": photo,
        "galerie": photo.galerie,
        "collection": photo.collection,
        "versions": versions,
        "version_defaut": version_defaut,
    }

    return render(request, "galeries/photo_detail.html", context)


def galerie_privee(request, galerie_slug):
    """Vue galerie privée - nécessite une authentification"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=False)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect("accueil:index")

    context = {"galerie": galerie, "est_prive": True}

    if galerie.a_des_collections():
        # Mode hiérarchique : afficher les collections (toutes, même non publiques pour les accès privés)
        context["collections"] = galerie.collections.order_by("ordre_affichage")

    # Photos directes (toutes, même non publiques)
    photos_directes = galerie.photos.filter(collection__isnull=True).order_by(
        "ordre_affichage"
    )
    if photos_directes.exists():
        context["photos"] = photos_directes

    return render(request, "galeries/galerie_detail.html", context)


def collection_privee(request, galerie_slug, collection_slug):
    """Vue collection privée - nécessite une authentification"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=False)
    collection = get_object_or_404(Collection, galerie=galerie, slug=collection_slug)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect("accueil:index")

    # Photos de la collection (toutes, même non publiques)
    photos = collection.photos.order_by("ordre_affichage")

    # Collections précédente et suivante
    collections_galerie = galerie.collections.order_by("ordre_affichage", "cree_le")
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
        "galerie": galerie,
        "collection": collection,
        "photos": photos,
        "prev_collection": prev_collection,
        "next_collection": next_collection,
        "est_prive": True,
    }

    return render(request, "galeries/collection_detail.html", context)


def photo_privee(request, photo_id):
    """Vue photo privée - nécessite une authentification"""
    photo = get_object_or_404(Photo, id=photo_id)

    # Vérifier que la photo appartient à une galerie privée
    if photo.galerie.est_publique:
        return redirect("galeries:photo_detail", photo_id=photo_id)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, photo.galerie):
        messages.error(request, "Accès non autorisé. Veuillez vous authentifier.")
        return redirect("accueil:index")

    versions = photo.versions.all()  # Toutes les versions pour les accès privés
    version_defaut = photo.get_version_par_defaut()

    context = {
        "photo": photo,
        "galerie": photo.galerie,
        "collection": photo.collection,
        "versions": versions,
        "version_defaut": version_defaut,
        "est_prive": True,
    }

    return render(request, "galeries/photo_detail.html", context)


def _verifier_acces_prive(request, galerie):
    """Vérifie si l'utilisateur a accès à la galerie privée"""
    token = request.session.get("visiteur_token")

    if not token:
        return False

    try:
        # Trouver le visiteur par son token
        visiteur = VisiteurGalerie.objects.get(token_acces=token, est_actif=True)

        # Chercher tous les accès de ce visiteur (même email) pour la galerie demandée
        visiteurs_meme_email = VisiteurGalerie.objects.filter(
            email=visiteur.email, est_actif=True
        ).select_related("acces_galerie")

        for v in visiteurs_meme_email:
            if (
                v.acces_galerie.galerie == galerie
                and v.acces_galerie.est_actif
                and v.acces_galerie.est_valide()
                and v.peut_acceder()
            ):
                # Mettre à jour la session avec le bon accès
                request.session["acces_galerie_id"] = v.acces_galerie.id
                return True

    except VisiteurGalerie.DoesNotExist:
        pass

    return False


def deconnexion_privee(request):
    """Déconnexion des galeries privées"""
    # Nettoyer la session
    if "visiteur_token" in request.session:
        del request.session["visiteur_token"]
    if "acces_galerie_id" in request.session:
        del request.session["acces_galerie_id"]

    messages.success(request, "Vous avez été déconnecté des galeries privées.")
    return redirect("accueil:index")


def tableau_bord_prive(request):
    """Tableau de bord des galeries privées accessibles au visiteur"""
    visiteur_token = request.session.get("visiteur_token")
    if not visiteur_token:
        messages.error(
            request, "Vous devez vous connecter pour accéder aux galeries privées."
        )
        return redirect("accueil:index")

    # Récupérer le visiteur
    visiteur = VisiteurGalerie.get_visiteur_par_token(visiteur_token)
    if not visiteur or not visiteur.peut_acceder():
        messages.error(request, "Votre accès n'est plus valide.")
        return redirect("galeries:deconnexion_privee")

    # Récupérer toutes les galeries accessibles à ce visiteur
    galeries_accessibles = VisiteurGalerie.get_galeries_accessibles(visiteur.email)

    # Informations sur le visiteur actuel
    context = {
        "visiteur": visiteur,
        "galeries_accessibles": galeries_accessibles,
        "galerie_courante": visiteur.acces_galerie.galerie,
        "est_prive": True,
    }

    return render(request, "galeries/tableau_bord_prive.html", context)


def telecharger_galerie_zip(request, galerie_slug):
    """Télécharge toutes les images d'une galerie privée en ZIP"""
    galerie = get_object_or_404(Galerie, slug=galerie_slug, est_publique=False)

    # Vérifier l'authentification
    if not _verifier_acces_prive(request, galerie):
        raise Http404("Accès non autorisé")

    # Récupérer toutes les photos de la galerie (directes + dans collections)
    photos = Photo.objects.filter(galerie=galerie)

    if not photos.exists():
        messages.error(
            request,
            f"La galerie '{galerie.nom}' ne contient aucune photo à télécharger.",
        )
        return redirect("galeries:galerie_privee", galerie_slug=galerie.slug)

    def generer_zip():
        """Générateur qui crée le ZIP en streaming"""
        # Créer un fichier temporaire pour le ZIP
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
                compteur_fichiers = {}  # Pour gérer les doublons de noms

                for photo in photos:
                    # Récupérer la meilleure version disponible
                    version = None

                    # Priorité : version HD couleur > version HD mono > version web couleur > version web mono
                    versions = photo.versions.all().order_by(
                        "-traitement"
                    )  # couleur avant monochrome

                    for v in versions:
                        if v.fichier_pleine_resolution:
                            version = v
                            break

                    if not version:
                        # Fallback sur version web
                        for v in versions:
                            if v.fichier_web:
                                version = v
                                break

                    if not version:
                        continue  # Passer cette photo si aucune version

                    # Construire le nom du fichier dans le ZIP
                    nom_base = photo.get_titre_affichage()
                    if photo.collection:
                        nom_base = f"{photo.collection.nom}_{nom_base}"

                    # Nettoyer le nom pour le système de fichiers
                    nom_propre = slugify(nom_base)
                    if not nom_propre:
                        nom_propre = f"photo_{photo.id}"

                    # Récupérer l'extension du fichier
                    fichier_source = (
                        version.fichier_pleine_resolution
                        if version.fichier_pleine_resolution
                        else version.fichier_web
                    )
                    extension = os.path.splitext(fichier_source.name or "")[1].lower()

                    # Gérer les doublons de noms
                    nom_fichier_zip = f"{nom_propre}{extension}"
                    if nom_fichier_zip in compteur_fichiers:
                        compteur_fichiers[nom_fichier_zip] += 1
                        nom_fichier_zip = f"{nom_propre}_{compteur_fichiers[nom_fichier_zip]}{extension}"
                    else:
                        compteur_fichiers[nom_fichier_zip] = 0

                    # Ajouter le fichier au ZIP
                    try:
                        if os.path.exists(fichier_source.path):
                            zip_file.write(fichier_source.path, nom_fichier_zip)
                    except Exception:
                        # En cas d'erreur, continuer avec les autres fichiers
                        continue

            # Lire le fichier ZIP créé et le streamer
            temp_file.seek(0)
            while True:
                chunk = temp_file.read(8192)
                if not chunk:
                    break
                yield chunk

    # Préparer la réponse de streaming
    nom_galerie_propre = slugify(galerie.nom)
    nom_fichier = f"{nom_galerie_propre}_photos.zip"

    response = StreamingHttpResponse(generer_zip(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'

    return response
