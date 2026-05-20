from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from galeries.models import AccesGalerie, Galerie, VisiteurGalerie

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

    # Récupérer la configuration de l'accueil
    from .models import AccueilConfig, SectionAccueil
    config = AccueilConfig.get_config()

    # Traiter le formulaire d'accès privé (AJAX)
    if request.method == 'POST' and ('email' in request.POST and 'code' in request.POST):
        email = request.POST.get('email', '').strip()
        code_acces = request.POST.get('code', '').upper().strip()

        if not email or not code_acces:
            return JsonResponse({
                'success': False,
                'error': 'Email et code d\'accès requis.'
            })

        try:
            # Rechercher l'accès galerie
            acces = AccesGalerie.objects.get(code_acces=code_acces)

            if not acces.est_valide():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce code d\'accès n\'est plus valide.'
                })

            # Vérifier que le visiteur est autorisé (ne pas créer automatiquement)
            try:
                visiteur = VisiteurGalerie.objects.get(
                    acces_galerie=acces,
                    email=email
                )
            except VisiteurGalerie.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Votre adresse email n\'est pas autorisée pour cette galerie.'
                })

            if not visiteur.peut_acceder():
                return JsonResponse({
                    'success': False,
                    'error': 'Votre accès à cette galerie a été désactivé.'
                })

            # Marquer la visite et incrémenter les compteurs
            visiteur.marquer_visite()
            acces.incrementer_acces()

            # Stocker le token en session
            request.session['visiteur_token'] = visiteur.token_acces
            request.session['acces_galerie_id'] = acces.id

            # Rediriger vers la galerie privée
            galerie_url = f'/galerie/prive/{acces.galerie.slug}/'
            return JsonResponse({
                'success': True,
                'message': f'Accès autorisé à la galerie : {acces.galerie.nom}',
                'redirect_url': galerie_url
            })

        except AccesGalerie.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Code d\'accès invalide.'
            })
        except Exception:
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors de la vérification. Veuillez réessayer.'
            })

    # Récupérer les galeries depuis la base de données
    galeries = Galerie.objects.filter(est_publique=True).order_by('ordre_affichage', 'nom')

    # Récupérer les sections personnalisées
    sections = SectionAccueil.objects.filter(est_active=True).order_by('position', 'ordre')

    context = {
        'galeries': galeries,
        'total_collections': galeries.count(),
        # Configuration dynamique
        'titre_site': config.titre_site,
        'sous_titre': config.sous_titre,
        'description': config.description,
        'hero_image': config.hero_image,
        'titre_galeries': config.titre_galeries,
        'titre_acces_prive': config.titre_acces_prive,
        'description_acces_prive': config.description_acces_prive,
        'modal_titre': config.modal_titre,
        'modal_sous_titre': config.modal_sous_titre,
        'modal_placeholder_code': config.modal_placeholder_code,
        # Sections personnalisées
        'sections': sections,
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

    # Récupérer la configuration de l'accueil
    from .models import AccueilConfig
    config = AccueilConfig.get_config()

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
                    'Erreur lors de l\'envoi du message. Veuillez réessayer ou me contacter directement à contact@horslemurs.fr'
                )
    else:
        form = ContactForm()

    context = {
        'form': form,
        'titre_site': config.titre_site,
        'sous_titre': config.sous_titre,
    }

    return render(request, 'accueil/contact.html', context)
