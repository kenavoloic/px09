"""
Vues d'administration pour la gestion de l'ordre des photos
"""

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Collection, Galerie, Photo


@staff_member_required
def photo_ordering_view(request):
    """Vue principale pour gérer l'ordre des photos"""

    # Récupérer la galerie ou collection sélectionnée
    galerie_id = request.GET.get("galerie")
    collection_id = request.GET.get("collection")

    context = {
        "title": "Gestion de l'ordre des photos",
        "galeries": Galerie.objects.all().order_by("nom"),
        "photos": [],
        "selected_galerie": None,
        "selected_collection": None,
    }

    if galerie_id:
        galerie = get_object_or_404(Galerie, id=galerie_id)
        context["selected_galerie"] = galerie
        context["collections"] = galerie.collections.all().order_by("nom")

        if collection_id:
            # Mode collection
            collection = get_object_or_404(
                Collection, id=collection_id, galerie=galerie
            )
            context["selected_collection"] = collection
            context["photos"] = collection.photos.filter(est_publique=True).order_by(
                "ordre_affichage"
            )
        else:
            # Mode galerie (photos directes)
            context["photos"] = galerie.photos.filter(
                collection__isnull=True, est_publique=True
            ).order_by("ordre_affichage")

    return render(request, "admin/galeries/photo_ordering.html", context)


@staff_member_required
@csrf_exempt
@require_POST
def update_photo_order(request):
    """API pour mettre à jour l'ordre des photos via AJAX"""

    try:
        data = json.loads(request.body)
        photo_ids = data.get("photo_ids", [])

        if not photo_ids:
            return JsonResponse({"error": "Aucune photo fournie"}, status=400)

        # Mettre à jour l'ordre des photos
        for index, photo_id in enumerate(photo_ids):
            try:
                photo = Photo.objects.get(id=photo_id)
                photo.ordre_affichage = index + 1
                photo.save(update_fields=["ordre_affichage"])
            except Photo.DoesNotExist:
                return JsonResponse(
                    {"error": f"Photo {photo_id} introuvable"}, status=404
                )

        return JsonResponse(
            {
                "success": True,
                "message": f"Ordre mis à jour pour {len(photo_ids)} photo(s)",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Format JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur serveur: {str(e)}"}, status=500)


@staff_member_required
def ajax_collections(request):
    """API AJAX pour récupérer les collections d'une galerie"""

    galerie_id = request.GET.get("galerie_id")
    if not galerie_id:
        return JsonResponse({"error": "ID galerie manquant"}, status=400)

    try:
        galerie = Galerie.objects.get(id=galerie_id)
        collections = [
            {
                "id": collection.id,
                "nom": collection.nom,
                "photo_count": collection.photos.count(),
            }
            for collection in galerie.collections.all().order_by("nom")
        ]

        return JsonResponse({"collections": collections, "galerie_nom": galerie.nom})

    except Galerie.DoesNotExist:
        return JsonResponse({"error": "Galerie introuvable"}, status=404)


@staff_member_required
@require_GET
def photo_thumbnail_api(request, photo_id):
    """API endpoint pour récupérer les informations de thumbnail d'une photo"""
    try:
        photo = get_object_or_404(Photo, id=photo_id)
        version = photo.get_version_par_defaut()

        data = {
            "id": photo.id,
            "title": photo.titre or f"Photo {photo.id}",
            "thumbnail_url": version.fichier_web.url
            if version and version.fichier_web
            else None,
            "collection": photo.collection.nom if photo.collection else "Photo directe",
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
