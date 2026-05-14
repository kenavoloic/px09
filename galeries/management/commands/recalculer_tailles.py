import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from galeries.models import PhotoVersion


class Command(BaseCommand):
    help = 'Recalcule les tailles de fichiers pour toutes les versions de photos existantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le recalcul même si les tailles sont déjà renseignées',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}Recalcul des tailles de fichiers..."
            )
        )

        # Récupérer les versions à traiter
        if force:
            versions = PhotoVersion.objects.all()
        else:
            versions = PhotoVersion.objects.filter(
                taille_fichier_web__isnull=True
            ).union(
                PhotoVersion.objects.filter(taille_fichier_hd__isnull=True)
            )

        total_versions = versions.count()
        if total_versions == 0:
            self.stdout.write(
                self.style.WARNING("Aucune version à traiter.")
            )
            return

        self.stdout.write(f"Versions à traiter : {total_versions}")

        updated_count = 0
        error_count = 0

        for i, version in enumerate(versions, 1):
            self.stdout.write(f"[{i}/{total_versions}] Traitement de {version}...", ending="")

            if dry_run:
                # Mode dry-run : affichage seulement
                taille_web = self._get_file_size(version.fichier_web)
                taille_hd = self._get_file_size(version.fichier_pleine_resolution)
                
                self.stdout.write(
                    f" Web: {self._format_size(taille_web) if taille_web else 'N/A'}, "
                    f"HD: {self._format_size(taille_hd) if taille_hd else 'N/A'}"
                )
                continue

            try:
                with transaction.atomic():
                    # Calculer les tailles
                    updated = False
                    
                    # Taille fichier web
                    if force or version.taille_fichier_web is None:
                        taille_web = self._get_file_size(version.fichier_web)
                        if taille_web is not None:
                            version.taille_fichier_web = taille_web
                            updated = True

                    # Taille fichier HD
                    if force or version.taille_fichier_hd is None:
                        taille_hd = self._get_file_size(version.fichier_pleine_resolution)
                        if taille_hd is not None:
                            version.taille_fichier_hd = taille_hd
                            updated = True

                    if updated:
                        # Utiliser update_fields pour éviter la boucle infinie avec save()
                        PhotoVersion.objects.filter(pk=version.pk).update(
                            taille_fichier_web=version.taille_fichier_web,
                            taille_fichier_hd=version.taille_fichier_hd
                        )
                        updated_count += 1
                        self.stdout.write(" ✓")
                    else:
                        self.stdout.write(" (aucun changement)")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f" Erreur : {str(e)}")
                )

        # Résumé
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nTerminé ! {updated_count} versions mises à jour, {error_count} erreurs."
                )
            )
            
            # Afficher les statistiques totales
            self._show_statistics()

    def _get_file_size(self, file_field):
        """Retourne la taille d'un fichier en octets ou None si erreur"""
        if not file_field:
            return None
            
        try:
            if hasattr(file_field, 'path'):
                return os.path.getsize(file_field.path)
        except (OSError, FileNotFoundError):
            pass
        
        return None

    def _format_size(self, size_bytes):
        """Formate une taille en octets vers une chaîne lisible"""
        if size_bytes is None:
            return "N/A"
        
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        
        for unit in units:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"

    def _show_statistics(self):
        """Affiche les statistiques globales"""
        from django.db.models import Sum, Count
        
        stats = PhotoVersion.objects.aggregate(
            total_versions=Count('id'),
            total_web=Sum('taille_fichier_web'),
            total_hd=Sum('taille_fichier_hd'),
            versions_avec_web=Count('id', filter=models.Q(taille_fichier_web__isnull=False)),
            versions_avec_hd=Count('id', filter=models.Q(taille_fichier_hd__isnull=False))
        )
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("STATISTIQUES GLOBALES")
        self.stdout.write("="*50)
        self.stdout.write(f"Total versions : {stats['total_versions']}")
        self.stdout.write(f"Versions avec fichier web : {stats['versions_avec_web']}")
        self.stdout.write(f"Versions avec fichier HD : {stats['versions_avec_hd']}")
        self.stdout.write(f"Taille totale fichiers web : {self._format_size(stats['total_web'] or 0)}")
        self.stdout.write(f"Taille totale fichiers HD : {self._format_size(stats['total_hd'] or 0)}")
        
        total_size = (stats['total_web'] or 0) + (stats['total_hd'] or 0)
        self.stdout.write(f"Taille totale : {self._format_size(total_size)}")