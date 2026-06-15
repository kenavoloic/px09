"""
Dashboard personnalisé pour l'administration
"""

from datetime import timedelta

from django.contrib.admin import AdminSite
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from commandes.models import Client, Commande

from .models import AccesGalerie, Collection, Galerie, Photo, VisiteurGalerie


class CustomAdminSite(AdminSite):
    """Site admin personnalisé avec dashboard"""

    site_header = "Hors les Murs - Administration"
    site_title = "Portfolio Admin"
    index_title = "Tableau de bord"

    def index(self, request, extra_context=None):
        """Page d'accueil personnalisée avec dashboard"""

        # Statistiques générales
        stats = self.get_dashboard_stats()

        # Activité récente
        activite_recente = self.get_activite_recente()

        # Galeries à compléter
        galeries_attention = self.get_galeries_attention()

        # Accès galeries privées
        acces_prives = self.get_acces_prives_stats()

        # Statistiques commandes
        commandes_stats = self.get_commandes_stats()

        extra_context = extra_context or {}
        extra_context.update(
            {
                "stats": stats,
                "activite_recente": activite_recente,
                "galeries_attention": galeries_attention,
                "acces_prives": acces_prives,
                "commandes_stats": commandes_stats,
                "actions_rapides": self.get_actions_rapides(),
            }
        )

        return render(request, "admin/dashboard/index.html", extra_context)

    def get_dashboard_stats(self):
        """Calcule les statistiques pour le dashboard"""

        # Galeries
        galeries_total = Galerie.objects.count()
        galeries_publiques = Galerie.objects.filter(est_publique=True).count()
        galeries_privees = galeries_total - galeries_publiques

        # Photos
        photos_stats = Photo.objects.aggregate(
            total=Count("id"),
            publiques=Count("id", filter=Q(est_publique=True)),
            directes=Count("id", filter=Q(collection__isnull=True)),
            collections=Count("id", filter=Q(collection__isnull=False)),
        )

        # Collections
        collections_total = Collection.objects.count()
        collections_publiques = Collection.objects.filter(est_publique=True).count()

        # Taille totale
        taille_totale = 0
        for galerie in Galerie.objects.all():
            taille_totale += galerie.get_taille_totale()

        # Formatage de la taille
        if taille_totale > 1024**3:
            taille_formatee = f"{taille_totale / (1024**3):.1f} GB"
        elif taille_totale > 1024**2:
            taille_formatee = f"{taille_totale / (1024**2):.1f} MB"
        else:
            taille_formatee = f"{taille_totale / 1024:.1f} KB"

        return {
            "galeries": {
                "total": galeries_total,
                "publiques": galeries_publiques,
                "privees": galeries_privees,
            },
            "photos": {
                "total": photos_stats["total"],
                "publiques": photos_stats["publiques"],
                "directes": photos_stats["directes"],
                "collections": photos_stats["collections"],
            },
            "collections": {
                "total": collections_total,
                "publiques": collections_publiques,
            },
            "stockage": {
                "taille_totale": taille_formatee,
                "taille_bytes": taille_totale,
            },
        }

    def get_activite_recente(self):
        """Récupère l'activité récente"""

        # Photos ajoutées récemment (7 derniers jours)
        semaine_passee = timezone.now() - timedelta(days=7)
        photos_recentes = (
            Photo.objects.filter(cree_le__gte=semaine_passee)
            .select_related("galerie", "collection")
            .order_by("-cree_le")[:10]
        )

        # Galeries modifiées récemment
        galeries_recentes = Galerie.objects.filter(
            modifie_le__gte=semaine_passee
        ).order_by("-modifie_le")[:5]

        # Accès galeries privées récents
        acces_recents = (
            VisiteurGalerie.objects.filter(date_dernier_acces__gte=semaine_passee)
            .select_related("acces_galerie__galerie")
            .order_by("-date_dernier_acces")[:5]
        )

        return {
            "photos_recentes": photos_recentes,
            "galeries_recentes": galeries_recentes,
            "acces_recents": acces_recents,
        }

    def get_galeries_attention(self):
        """Galeries qui nécessitent de l'attention"""

        # Galeries vides
        galeries_vides = Galerie.objects.annotate(nb_photos=Count("photos")).filter(
            nb_photos=0
        )

        # Galeries sans photo de couverture
        galeries_sans_couverture = (
            Galerie.objects.exclude(photos__est_couverture=True)
            .annotate(nb_photos=Count("photos"))
            .filter(nb_photos__gt=0)
        )

        # Photos sans titre dans galeries publiques
        photos_sans_titre = Photo.objects.filter(
            titre__isnull=True, galerie__est_publique=True, est_publique=True
        ).count()

        return {
            "galeries_vides": galeries_vides,
            "galeries_sans_couverture": galeries_sans_couverture,
            "photos_sans_titre": photos_sans_titre,
        }

    def get_acces_prives_stats(self):
        """Statistiques sur les accès aux galeries privées"""

        acces_actifs = AccesGalerie.objects.filter(est_actif=True).count()
        visiteurs_actifs = VisiteurGalerie.objects.filter(est_actif=True).count()

        # Accès qui expirent bientôt (dans 7 jours)
        expiration_proche = timezone.now() + timedelta(days=7)
        acces_expirant = AccesGalerie.objects.filter(
            est_actif=True,
            date_expiration__lte=expiration_proche,
            date_expiration__gte=timezone.now(),
        )

        return {
            "acces_actifs": acces_actifs,
            "visiteurs_actifs": visiteurs_actifs,
            "acces_expirant": acces_expirant,
        }

    def get_commandes_stats(self):
        """Statistiques sur les commandes clients"""

        # Statistiques générales
        commandes_total = Commande.objects.count()
        clients_total = Client.objects.count()

        # Commandes par statut
        commandes_en_cours = Commande.objects.filter(statut="en_cours").count()
        commandes_livrees = Commande.objects.filter(statut="livree").count()

        # Commandes récentes (7 derniers jours)
        semaine_passee = timezone.now() - timedelta(days=7)
        commandes_recentes = Commande.objects.filter(
            cree_le__gte=semaine_passee
        ).order_by("-cree_le")[:5]

        # Commandes qui expirent bientôt
        expiration_proche = timezone.now() + timedelta(days=7)
        commandes_expirant = Commande.objects.filter(
            expire_le__lte=expiration_proche,
            expire_le__gte=timezone.now(),
            statut__in=["en_cours", "prete"],
        )

        return {
            "total": commandes_total,
            "clients": clients_total,
            "en_cours": commandes_en_cours,
            "livrees": commandes_livrees,
            "recentes": commandes_recentes,
            "expirant": commandes_expirant,
        }

    def get_actions_rapides(self):
        """Actions rapides pour le dashboard"""
        return [
            {
                "titre": "📷 Upload de photos",
                "description": "Ajouter de nouvelles photos",
                "url": "galeries_admin:upload_photos",
                "couleur": "blue",
            },
            {
                "titre": "🖼️ Nouvelle galerie",
                "description": "Créer une nouvelle galerie",
                "url": "admin:galeries_galerie_add",
                "couleur": "green",
            },
            {
                "titre": "📁 Nouvelle collection",
                "description": "Organiser des photos",
                "url": "admin:galeries_collection_add",
                "couleur": "purple",
            },
            {
                "titre": "🛒 Nouvelle commande",
                "description": "Créer une commande client",
                "url": "admin:commandes_commande_add",
                "couleur": "orange",
            },
            {
                "titre": "🔐 Accès privé",
                "description": "Gérer les accès galeries",
                "url": "admin:galeries_accesgalerie_add",
                "couleur": "gray",
            },
        ]


# CustomAdminSite est instancié par Django comme site d'admin par défaut
# (admin.site), via configurations.admin_apps.CustomAdminConfig.default_site.
# Les modèles sont enregistrés par leurs décorateurs @admin.register lors de
# l'autodiscovery — aucun enregistrement explicite n'est nécessaire ici.
