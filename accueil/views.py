from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from galeries.models import Galerie

from .forms import ContactForm

# Données des galeries centralisées
GALERIES_DATA = [
    {
        'nom': 'PAYSAGE',
        'slug': 'paysage',
        'label': 'paysage',
        'nb_photos': 34,
        'description': 'Des paysages naturels capturés dans leur beauté brute et authentique.',
    },
    {
        'nom': 'SPORT',
        'slug': 'sport',
        'label': 'sport',
        'nb_photos': 48,
        'description': 'L\'énergie et la passion du sport immortalisées en mouvement.',
    },
    {
        'nom': 'ARCHITECTURE',
        'slug': 'architecture',
        'label': 'architecture',
        'nb_photos': 27,
        'description': 'Structures et formes architecturales sous un nouveau regard.',
    },
    {
        'nom': 'DOCUMENTAIRE',
        'slug': 'documentaire',
        'label': 'documentaire',
        'nb_photos': 56,
        'description': 'Témoignages visuels de la vie et des histoires humaines.',
    },
    # {
    #     'nom': 'URBAIN',
    #     'slug': 'urbain',
    #     'label': 'urbain',
    #     'nb_photos': 41,
    #     'description': 'La ville et ses habitants dans leur quotidien urbain.',
    # },
    {
        'nom': 'NATURE',
        'slug': 'nature',
        'label': 'nature',
        'nb_photos': 29,
        'description': 'La nature dans ses détails les plus intimes et sauvages.',
    },
]


def index(request: HttpRequest) -> HttpResponse:
    """Vue pour la page d'accueil du studio photographique."""

    # Récupérer les galeries depuis la base de données
    galeries = Galerie.objects.filter(est_publique=True).order_by('ordre_affichage', 'nom')

    context = {
        'galeries': galeries,
        'total_collections': galeries.count(),
        'titre_site': 'HORS LES MURS',
        'sous_titre': 'Studio photographique',
        'description': 'Paysages, architecture, sport, documentaire. Des images capturées hors des sentiers battus, là où la lumière raconte.',
    }

    return render(request, 'accueil/index.html', context)


def galerie_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Vue pour afficher une galerie spécifique."""
    # Trouver la galerie par slug
    galerie = None
    for g in GALERIES_DATA:
        if g['slug'] == slug:
            galerie = g
            break

    if not galerie:
        raise Http404("Galerie non trouvée")

    # Obtenir les autres galeries pour la section "Autres galeries", triées par ordre alphabétique
    autres_galeries = sorted([g for g in GALERIES_DATA if g['slug'] != slug], key=lambda x: str(x['nom']))

    context = {
        'galerie': galerie,
        'galeries': autres_galeries,
        'titre_site': 'HORS LES MURS',
        'sous_titre': 'Studio photographique',
    }

    return render(request, 'accueil/galerie_detail.html', context)


def contact(request: HttpRequest) -> HttpResponse:
    """Vue pour le formulaire de contact."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            if form.send_email():
                messages.success(
                    request,
                    'Votre message a bien été envoyé ! Je vous répondrai dans les plus brefs délais.'
                )
                return redirect('accueil:contact')
            else:
                messages.error(
                    request,
                    'Erreur lors de l\'envoi du message. Veuillez réessayer ou me contacter directement.'
                )
    else:
        form = ContactForm()

    context = {
        'form': form,
        'titre_site': 'HORS LES MURS',
        'sous_titre': 'Studio photographique',
    }

    return render(request, 'accueil/contact.html', context)
