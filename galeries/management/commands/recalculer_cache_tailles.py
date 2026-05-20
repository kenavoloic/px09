from django.core.management.base import BaseCommand

from galeries.models import Collection, Galerie, PhotoVersion


class Command(BaseCommand):
    help = 'Recalcule le cache des tailles pour toutes les galeries et collections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}Recalcul du cache des tailles..."
            )
        )

        # Recalculer pour toutes les galeries
        galeries = Galerie.objects.all()
        self.stdout.write(f"Galeries à traiter : {galeries.count()}")

        for galerie in galeries:
            if dry_run:
                taille_calculee = galerie.get_taille_totale()
                self.stdout.write(
                    f"  {galerie.nom}: cache={galerie.taille_totale_cache} -> {taille_calculee} "
                    f"({PhotoVersion.format_taille(taille_calculee)})"
                )
            else:
                galerie.recalculer_taille_cache()
                self.stdout.write(
                    f"  ✓ {galerie.nom}: {galerie.get_taille_totale_formatee()}"
                )

        # Recalculer pour toutes les collections
        collections = Collection.objects.all()
        self.stdout.write(f"\nCollections à traiter : {collections.count()}")

        for collection in collections:
            if dry_run:
                taille_calculee = collection.get_taille_totale()
                self.stdout.write(
                    f"  {collection.galerie.nom}/{collection.nom}: "
                    f"cache={collection.taille_totale_cache} -> {taille_calculee} "
                    f"({PhotoVersion.format_taille(taille_calculee)})"
                )
            else:
                collection.recalculer_taille_cache()
                self.stdout.write(
                    f"  ✓ {collection.galerie.nom}/{collection.nom}: {collection.get_taille_totale_formatee()}"
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nTerminé ! Cache mis à jour pour {galeries.count()} galeries "
                    f"et {collections.count()} collections."
                )
            )
        else:
            self.stdout.write("\n[DRY RUN] Aucune modification effectuée.")


