"""
Signaux pour le traitement automatique des images
"""
import os
from io import BytesIO
from typing import Any

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image

from .models import PhotoVersion


@receiver(post_save, sender=PhotoVersion)
def optimize_photo_version(sender: type, instance: PhotoVersion, created: bool, **kwargs: Any) -> None:
    """
    Optimise automatiquement une PhotoVersion après sa création
    """
    if not created or not instance.fichier_web:
        return

    try:
        # Ouvrir l'image avec Pillow
        img = Image.open(instance.fichier_web.path)

        # Informations originales
        original_size = os.path.getsize(instance.fichier_web.path)
        original_width, original_height = img.size

        # Optimisation selon la taille
        optimized = False

        # Si l'image est très grande (> 1920px), la redimensionner
        if original_width > 1920:
            # Calculer les nouvelles dimensions en gardant le ratio
            ratio = 1920 / original_width
            new_width = 1920
            new_height = int(original_height * ratio)

            # Redimensionner avec une qualité optimale
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Mettre à jour les dimensions dans la base
            instance.largeur = new_width
            instance.hauteur = new_height
            optimized = True

        # Optimiser la compression JPEG
        if img.format == 'JPEG' or optimized:
            # Convertir en RGB si nécessaire (pour éviter les erreurs JPEG)
            if img.mode in ('RGBA', 'P'):
                # Créer un fond blanc pour la transparence
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # Sauvegarder avec optimisation
            output = BytesIO()

            # Qualité adaptive selon la taille finale
            if img.width > 1200:
                quality = 90  # Haute qualité pour grandes images
            elif img.width > 800:
                quality = 88  # Qualité moyenne-haute
            else:
                quality = 85  # Qualité standard

            img.save(
                output,
                format='JPEG',
                quality=quality,
                optimize=True,
                progressive=True  # JPEG progressif pour un meilleur chargement
            )

            # Créer un nouveau fichier Django
            output.seek(0)
            optimized_file = InMemoryUploadedFile(
                output,
                None,
                instance.fichier_web.name,
                'image/jpeg',
                output.tell(),
                None
            )

            # Sauvegarder le fichier optimisé
            instance.fichier_web.save(
                instance.fichier_web.name,
                optimized_file,
                save=False
            )

            # Calculer les gains
            if optimized:
                new_size = os.path.getsize(instance.fichier_web.path)
                reduction_percent = ((original_size - new_size) / original_size) * 100

                print(f"✅ Image optimisée: {instance.photo.titre}")
                print(f"   Taille: {original_width}x{original_height} → {instance.largeur}x{instance.hauteur}")
                print(f"   Poids: {original_size/1024/1024:.1f}MB → {new_size/1024/1024:.1f}MB (-{reduction_percent:.1f}%)")

        # Sauvegarder les nouvelles dimensions si modifiées
        if optimized:
            instance.save(update_fields=['largeur', 'hauteur'])

    except Exception as e:
        print(f"⚠️  Erreur lors de l'optimisation de {instance.photo.titre}: {e}")
        # Ne pas faire échouer la sauvegarde en cas d'erreur d'optimisation
        pass


@receiver(post_save, sender=PhotoVersion)
def generate_thumbnail_preview(sender: type, instance: PhotoVersion, created: bool, **kwargs: Any) -> None:
    """
    Pré-génère les thumbnails pour améliorer les performances
    """
    if not created or not instance.fichier_web:
        return

    try:
        # Forcer la génération des versions ImageSpecField
        # Cela va créer les fichiers sur disque immédiatement
        _ = instance.thumbnail.url  # Déclenche la génération du thumbnail
        _ = instance.gallery_preview.url  # Déclenche la génération du preview

        print(f"🖼️  Thumbnails générés pour: {instance.photo.titre}")

    except Exception as e:
        print(f"⚠️  Erreur lors de la génération des thumbnails pour {instance.photo.titre}: {e}")
        pass
