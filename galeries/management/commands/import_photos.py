"""
Commande de management pour importer des photos depuis le dossier media/raw/
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from django.core.files import File
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from PIL import Image

from galeries.models import Galerie, Photo, PhotoVersion

try:
    import pyexiv2
    PYEXIV2_AVAILABLE = True
except ImportError:
    PYEXIV2_AVAILABLE = False


class Command(BaseCommand):
    help = 'Import photos from media/raw/ directory with EXIF analysis'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--galerie',
            type=str,
            help='Slug of the gallery to import photos into (required)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of photos to import'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options['dry_run']
        galerie_slug = options['galerie']
        limit = options['limit']

        if not galerie_slug:
            self.stdout.write(
                self.style.ERROR('--galerie is required. Use an existing gallery slug.')
            )
            return

        # Vérifier que la galerie existe
        try:
            galerie = Galerie.objects.get(slug=galerie_slug)
        except Galerie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Gallery with slug "{galerie_slug}" not found.')
            )
            self.stdout.write('Available galleries:')
            for g in Galerie.objects.all():
                self.stdout.write(f'  - {g.slug} ({g.nom})')
            return

        # Dossier source des photos
        raw_dir = Path('media/raw')
        if not raw_dir.exists():
            self.stdout.write(self.style.ERROR(f'Directory {raw_dir} does not exist'))
            return

        # Trouver toutes les photos
        photo_files = list(raw_dir.glob('*.jpg')) + list(raw_dir.glob('*.JPG'))
        
        if limit:
            photo_files = photo_files[:limit]

        self.stdout.write(
            f'Found {len(photo_files)} photos to import into gallery "{galerie.nom}"'
        )

        if not PYEXIV2_AVAILABLE:
            self.stdout.write(
                self.style.WARNING('pyexiv2 not available. EXIF data will not be extracted.')
            )

        # Import des photos
        imported_count = 0
        for photo_path in photo_files:
            try:
                if dry_run:
                    self._analyze_photo(photo_path)
                else:
                    self._import_photo(photo_path, galerie)
                    imported_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {photo_path.name}: {str(e)}')
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} photos')
            )

    def _analyze_photo(self, photo_path: Path) -> None:
        """Analyse une photo et affiche ses informations"""
        self.stdout.write(f'\n📸 {photo_path.name}')
        
        # Informations de base
        stat = photo_path.stat()
        self.stdout.write(f'  Size: {stat.st_size / 1024 / 1024:.1f} MB')
        
        # Dimensions avec PIL
        try:
            with Image.open(photo_path) as img:
                self.stdout.write(f'  Dimensions: {img.width} x {img.height}')
                self.stdout.write(f'  Format: {img.format}')
        except Exception as e:
            self.stdout.write(f'  Error reading image: {e}')

        # EXIF avec pyexiv2
        if PYEXIV2_AVAILABLE:
            try:
                with pyexiv2.Image(str(photo_path)) as img:
                    exif = img.read_exif()
                    
                    # Date de prise de vue
                    if 'Exif.Photo.DateTimeOriginal' in exif:
                        self.stdout.write(f'  Date taken: {exif["Exif.Photo.DateTimeOriginal"]}')
                    
                    # Appareil photo
                    if 'Exif.Image.Make' in exif and 'Exif.Image.Model' in exif:
                        camera = f'{exif["Exif.Image.Make"]} {exif["Exif.Image.Model"]}'
                        self.stdout.write(f'  Camera: {camera}')
                    
                    # Objectif
                    if 'Exif.Photo.LensModel' in exif:
                        self.stdout.write(f'  Lens: {exif["Exif.Photo.LensModel"]}')
                    
                    # Paramètres de prise de vue
                    settings = []
                    if 'Exif.Photo.FNumber' in exif:
                        settings.append(f'f/{exif["Exif.Photo.FNumber"]}')
                    if 'Exif.Photo.ExposureTime' in exif:
                        settings.append(f'{exif["Exif.Photo.ExposureTime"]}s')
                    if 'Exif.Photo.ISOSpeedRatings' in exif:
                        settings.append(f'ISO {exif["Exif.Photo.ISOSpeedRatings"]}')
                    
                    if settings:
                        self.stdout.write(f'  Settings: {" | ".join(settings)}')
                        
            except Exception as e:
                self.stdout.write(f'  EXIF error: {e}')

    def _extract_exif_data(self, photo_path: Path) -> dict[str, Any]:
        """Extrait les données EXIF d'une photo"""
        exif_data = {}
        
        if not PYEXIV2_AVAILABLE:
            return exif_data

        try:
            with pyexiv2.Image(str(photo_path)) as img:
                exif = img.read_exif()
                
                # Date de prise de vue
                if 'Exif.Photo.DateTimeOriginal' in exif:
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
                
                # Ouverture
                if 'Exif.Photo.FNumber' in exif:
                    exif_data['ouverture'] = f'f/{exif["Exif.Photo.FNumber"]}'
                
                # Vitesse
                if 'Exif.Photo.ExposureTime' in exif:
                    exif_data['vitesse'] = f'{exif["Exif.Photo.ExposureTime"]}s'
                
                # ISO
                if 'Exif.Photo.ISOSpeedRatings' in exif:
                    exif_data['iso'] = int(exif['Exif.Photo.ISOSpeedRatings'])
                    
        except Exception as e:
            self.stdout.write(f'Warning: EXIF extraction failed for {photo_path.name}: {e}')
        
        return exif_data

    @transaction.atomic
    def _import_photo(self, photo_path: Path, galerie: Galerie) -> None:
        """Importe une photo dans la galerie"""
        
        # Extraire les données EXIF
        exif_data = self._extract_exif_data(photo_path)
        
        # Obtenir les dimensions avec PIL
        with Image.open(photo_path) as img:
            width, height = img.size
        
        # Créer l'objet Photo
        photo = Photo(
            galerie=galerie,
            titre=photo_path.stem.replace('_', ' '),  # Nom de fichier comme titre
            largeur_originale=width,
            hauteur_originale=height,
            ordre_affichage=galerie.get_total_photos() + 1
        )
        
        # Appliquer les données EXIF si disponibles
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
        # Pour l'instant, on copie directement le fichier original
        with open(photo_path, 'rb') as f:
            django_file = File(f)
            django_file.name = photo_path.name
            
            photo_version = PhotoVersion(
                photo=photo,
                traitement='couleur',
                largeur=width,
                hauteur=height,
                est_par_defaut=True
            )
            
            # Sauvegarder dans photos/web/ pour commencer
            photo_version.fichier_web.save(
                photo_path.name,
                django_file,
                save=False
            )
            
            photo_version.save()
        
        self.stdout.write(f'✅ Imported {photo_path.name}')