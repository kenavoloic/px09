"""
Vues d'administration personnalisées pour l'upload de photos
"""
import os
from pathlib import Path
from typing import Any

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files import File
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from PIL import Image

from .models import Galerie, Photo, PhotoVersion

try:
    import pyexiv2
    PYEXIV2_AVAILABLE = True
except ImportError:
    PYEXIV2_AVAILABLE = False


@staff_member_required
def upload_photos_view(request: HttpRequest) -> HttpResponse:
    """Vue d'upload de photos en masse pour l'admin"""
    
    if request.method == 'POST':
        galerie_id = request.POST.get('galerie')
        uploaded_files = request.FILES.getlist('photos')
        
        if not galerie_id or not uploaded_files:
            messages.error(request, 'Veuillez sélectionner une galerie et au moins une photo.')
            return redirect('galeries_admin:upload_photos')
        
        try:
            galerie = Galerie.objects.get(id=galerie_id)
        except Galerie.DoesNotExist:
            messages.error(request, 'Galerie introuvable.')
            return redirect('galeries_admin:upload_photos')
        
        # Import des photos
        imported_count = 0
        errors = []
        
        for uploaded_file in uploaded_files:
            try:
                with transaction.atomic():
                    # Validation basique du fichier
                    if not uploaded_file.content_type.startswith('image/'):
                        errors.append(f'{uploaded_file.name}: Type de fichier non supporté')
                        continue
                    
                    # Sauvegarder temporairement pour traitement
                    temp_path = Path('/tmp') / uploaded_file.name
                    with open(temp_path, 'wb') as f:
                        for chunk in uploaded_file.chunks():
                            f.write(chunk)
                    
                    # Extraire les métadonnées
                    exif_data = _extract_exif_data(temp_path)
                    
                    # Obtenir les dimensions
                    with Image.open(temp_path) as img:
                        width, height = img.size
                    
                    # Créer l'objet Photo
                    photo = Photo(
                        galerie=galerie,
                        nom_fichier=uploaded_file.name,
                        titre="",  # Pas de titre par défaut
                        largeur_originale=width,
                        hauteur_originale=height,
                        ordre_affichage=galerie.get_total_photos() + 1
                    )
                    
                    # Appliquer les données EXIF
                    if 'date_prise' in exif_data:
                        photo.date_prise = exif_data['date_prise']
                    if 'appareil' in exif_data:
                        photo.appareil = exif_data['appareil']
                    if 'objectif' in exif_data:
                        photo.objectif = exif_data['objectif']
                    if 'ouverture' in exif_data:
                        photo.ouverture = exif_data['ouverture']
                    if 'vitesse' in exif_data:
                        photo.vitesse = exif_data['vitesse']
                    if 'iso' in exif_data:
                        photo.iso = exif_data['iso']
                    
                    photo.save()
                    
                    # Créer la PhotoVersion
                    photo_version = PhotoVersion(
                        photo=photo,
                        traitement='couleur',
                        largeur=width,
                        hauteur=height,
                        est_par_defaut=True
                    )
                    
                    # Sauvegarder le fichier uploadé
                    with open(temp_path, 'rb') as f:
                        django_file = File(f)
                        photo_version.fichier_web.save(
                            uploaded_file.name,
                            django_file,
                            save=False
                        )
                    
                    photo_version.save()
                    
                    # Nettoyer le fichier temporaire
                    temp_path.unlink(missing_ok=True)
                    
                    imported_count += 1
                    
            except Exception as e:
                errors.append(f'{uploaded_file.name}: {str(e)}')
        
        # Messages de retour
        if imported_count > 0:
            messages.success(
                request,
                f'{imported_count} photo(s) importée(s) avec succès dans "{galerie.nom}".'
            )
        
        if errors:
            for error in errors[:5]:  # Limiter à 5 erreurs affichées
                messages.error(request, error)
            if len(errors) > 5:
                messages.error(request, f'... et {len(errors) - 5} autre(s) erreur(s).')
        
        return redirect('galeries_admin:upload_photos')
    
    # GET: Afficher le formulaire
    galeries = Galerie.objects.all().order_by('nom')
    
    context = {
        'title': 'Upload de photos',
        'galeries': galeries,
    }
    
    return render(request, 'admin/galeries/upload_photos.html', context)


def _extract_exif_data(photo_path: Path) -> dict[str, Any]:
    """Extrait les données EXIF d'une photo (similaire au script d'import)"""
    exif_data = {}
    
    if not PYEXIV2_AVAILABLE:
        return exif_data

    try:
        with pyexiv2.Image(str(photo_path)) as img:
            exif = img.read_exif()
            
            # Date de prise de vue
            if 'Exif.Photo.DateTimeOriginal' in exif:
                from datetime import datetime
                try:
                    date_str = exif['Exif.Photo.DateTimeOriginal']
                    exif_data['date_prise'] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    pass
            
            # Appareil photo
            if 'Exif.Image.Make' in exif and 'Exif.Image.Model' in exif:
                make = exif['Exif.Image.Make'].strip()
                model = exif['Exif.Image.Model'].strip()
                exif_data['appareil'] = f'{make} {model}'
            
            # Objectif
            if 'Exif.Photo.LensModel' in exif:
                exif_data['objectif'] = exif['Exif.Photo.LensModel']
            
            # Paramètres de prise de vue
            if 'Exif.Photo.FNumber' in exif:
                exif_data['ouverture'] = f'f/{exif["Exif.Photo.FNumber"]}'
            
            if 'Exif.Photo.ExposureTime' in exif:
                exif_data['vitesse'] = f'{exif["Exif.Photo.ExposureTime"]}s'
            
            if 'Exif.Photo.ISOSpeedRatings' in exif:
                exif_data['iso'] = int(exif['Exif.Photo.ISOSpeedRatings'])
                
    except Exception:
        pass  # Ignorer les erreurs EXIF silencieusement
    
    return exif_data