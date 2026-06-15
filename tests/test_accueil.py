from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from accueil.forms import ContactForm
from accueil.models import AccueilConfig, SectionAccueil
from galeries.models import Galerie


class AccueilConfigModelTest(TestCase):
    """Tests pour le modele AccueilConfig"""

    def test_get_config_cree_instance_par_defaut(self):
        """Test que get_config() cree une instance par defaut si necessaire"""
        self.assertEqual(AccueilConfig.objects.count(), 0)

        config = AccueilConfig.get_config()

        self.assertEqual(AccueilConfig.objects.count(), 1)
        self.assertEqual(config.pk, 1)
        self.assertEqual(config.titre_site, "HORS LES MURS")

    def test_get_config_retourne_instance_existante(self):
        """Test que get_config() retourne l'instance existante"""
        config1 = AccueilConfig.get_config()
        config2 = AccueilConfig.get_config()

        self.assertEqual(config1, config2)
        self.assertEqual(AccueilConfig.objects.count(), 1)

    def test_save_empeche_creation_multiple_instances(self):
        """Test qu'on ne peut pas creer plusieurs instances d'AccueilConfig"""
        AccueilConfig.objects.create()

        with self.assertRaises(ValidationError):
            AccueilConfig().save()

    def test_str_representation(self):
        """Test de la representation string"""
        config = AccueilConfig.get_config()
        config.titre_site = "Mon Site"

        self.assertEqual(str(config), "Configuration accueil - Mon Site")

    def test_valeurs_par_defaut(self):
        """Test des valeurs par defaut du modele"""
        config = AccueilConfig.get_config()

        self.assertEqual(config.titre_site, "HORS LES MURS")
        self.assertEqual(config.sous_titre, "Studio photographique")
        self.assertIn("Paysages, architecture", config.description)
        self.assertEqual(config.titre_galeries, "Galeries")
        self.assertEqual(config.titre_acces_prive, "Galeries privées")
        self.assertEqual(config.modal_titre, "Galerie privée")
        self.assertEqual(config.modal_placeholder_code, "ex: HLM-2024-XXX")


class SectionAccueilModelTest(TestCase):
    """Tests pour le modele SectionAccueil"""

    def test_creation_section(self):
        """Test de creation d'une section"""
        section = SectionAccueil.objects.create(
            titre="Ma Section",
            contenu="<p>Contenu de test</p>",
            position="hero",
            ordre=1,
        )

        self.assertEqual(section.titre, "Ma Section")
        self.assertEqual(section.position, "hero")
        self.assertTrue(section.est_active)

    def test_str_representation(self):
        """Test de la representation string"""
        section = SectionAccueil.objects.create(
            titre="Test Section", contenu="Contenu", position="galeries"
        )

        self.assertEqual(str(section), "Test Section (Avant les galeries)")

    def test_ordering(self):
        """Test de l'ordre des sections"""
        section2 = SectionAccueil.objects.create(
            titre="Section 2", contenu="Contenu", position="hero", ordre=2
        )
        section1 = SectionAccueil.objects.create(
            titre="Section 1", contenu="Contenu", position="hero", ordre=1
        )

        sections = list(SectionAccueil.objects.all())
        self.assertEqual(sections[0], section1)
        self.assertEqual(sections[1], section2)


class AccueilViewsTest(TestCase):
    """Tests pour les vues de l'application accueil"""

    def setUp(self):
        self.client = Client()
        self.galerie = Galerie.objects.create(
            nom="Test Galerie",
            slug="test-galerie",
            description="Une galerie de test",
            est_publique=True,
            ordre_affichage=1,
        )

    def test_index_view_GET(self):
        """Test de la vue index"""
        url = reverse("accueil:index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HORS LES MURS")
        self.assertIn("galeries", response.context)

    def test_index_view_avec_galeries(self):
        """Test que les galeries publiques sont affichees"""
        # Creer une galerie privee qui ne doit pas apparaitre
        Galerie.objects.create(
            nom="Galerie Privée",
            slug="privee",
            description="Privée",
            est_publique=False,
        )

        url = reverse("accueil:index")
        response = self.client.get(url)

        galeries = response.context["galeries"]
        self.assertEqual(galeries.count(), 1)
        self.assertEqual(galeries.first().nom, "Test Galerie")

    def test_index_view_avec_sections_personnalisees(self):
        """Test que les sections personnalisees sont incluses"""
        section = SectionAccueil.objects.create(
            titre="Section Test",
            contenu="<p>Contenu test</p>",
            position="hero",
            est_active=True,
        )

        url = reverse("accueil:index")
        response = self.client.get(url)

        sections = response.context["sections"]
        self.assertIn(section, sections)

    def test_contact_view_GET(self):
        """Test de la vue contact en GET"""
        url = reverse("accueil:contact")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ContactForm)

    def test_contact_view_POST_valide(self):
        """Test du formulaire de contact avec donnees valides"""
        url = reverse("accueil:contact")
        data = {
            "nom": "Dupont",
            "email": "test@example.com",
            "sujet": "info",
            "message": "Message de test",
        }

        response = self.client.post(url, data)

        # Peut etre 302 (redirection) ou 200 selon l'envoi email
        self.assertIn(response.status_code, [200, 302])

    def test_contact_view_POST_invalide(self):
        """Test du formulaire de contact avec donnees invalides"""
        url = reverse("accueil:contact")
        data = {
            "nom": "",  # Nom requis
            "email": "email-invalide",
            "sujet": "",
            "message": "",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)


class ContactFormTest(TestCase):
    """Tests pour le formulaire de contact"""

    def test_formulaire_valide(self):
        """Test d'un formulaire valide"""
        form_data = {
            "nom": "Dupont",
            "email": "test@example.com",
            "sujet": "info",
            "message": "Bonjour, j'aimerais avoir des informations.",
        }

        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulaire_invalide_email(self):
        """Test avec email invalide"""
        form_data = {
            "nom": "Dupont",
            "email": "email-invalide",
            "sujet": "info",
            "message": "Message",
        }

        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_formulaire_champs_requis(self):
        """Test des champs requis"""
        form = ContactForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("nom", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("sujet", form.errors)
        self.assertIn("message", form.errors)

    def test_formulaire_longueur_maximale(self):
        """Test des longueurs maximales"""
        form_data = {
            "nom": "x" * 101,  # Max 100
            "email": "test@example.com",
            "sujet": "info",
            "message": "x" * 1001,  # Max 1000
        }

        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("nom", form.errors)
        self.assertIn("message", form.errors)
