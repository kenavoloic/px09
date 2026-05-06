"""
Tests pour le formulaire de contact
"""
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accueil.forms import ContactForm


class TestContactForm(TestCase):
    """Tests pour le formulaire de contact"""

    def test_contact_form_valid_data(self):
        """Test avec des données valides"""
        form = ContactForm({
            'nom': 'Jean Dupont',
            'email': 'jean@example.com',
            'sujet': 'devis',
            'message': 'Bonjour, je souhaite un devis pour mon mariage.',
            'website': ''  # honeypot vide
        })

        self.assertTrue(form.is_valid())

    def test_contact_form_honeypot_spam(self):
        """Test détection spam via honeypot"""
        form = ContactForm({
            'nom': 'Spam Bot',
            'email': 'spam@bot.com',
            'sujet': 'devis',
            'message': 'Spam message',
            'website': 'http://spam.com'  # honeypot rempli = spam
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Spam détecté.', str(form.errors))

    def test_contact_form_required_fields(self):
        """Test champs obligatoires"""
        form = ContactForm({})

        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('sujet', form.errors)
        self.assertIn('message', form.errors)

    def test_contact_form_email_invalid(self):
        """Test email invalide"""
        form = ContactForm({
            'nom': 'Test',
            'email': 'email-invalide',
            'sujet': 'devis',
            'message': 'Test',
            'website': ''
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TestContactView(TestCase):
    """Tests pour la vue de contact"""

    def test_contact_page_accessible(self):
        """Test que la page contact est accessible"""
        response = self.client.get(reverse('accueil:contact'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Envoyez-moi un message')
        self.assertContains(response, 'form')

    def test_contact_form_submission_success(self):
        """Test envoi réussi du formulaire"""
        # Clear outbox before test
        mail.outbox = []

        response = self.client.post(reverse('accueil:contact'), {
            'nom': 'Jean Test',
            'email': 'jean.test@example.com',
            'sujet': 'devis',
            'message': 'Test de contact depuis les tests automatisés.',
            'website': ''  # honeypot vide
        })

        # Doit rediriger après succès
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accueil:contact'))

        # Dois y avoir 2 emails envoyés (photographe + confirmation)
        self.assertEqual(len(mail.outbox), 2)

        # Vérifier email au photographe
        email_photographe = mail.outbox[0]
        self.assertIn('[Portfolio]', email_photographe.subject)
        self.assertIn('Jean Test', email_photographe.body)
        self.assertEqual(email_photographe.to, ['contact@horslemurs.fr'])

        # Vérifier email de confirmation
        email_confirmation = mail.outbox[1]
        self.assertIn('bien été envoyé', email_confirmation.subject)
        self.assertEqual(email_confirmation.to, ['jean.test@example.com'])

    def test_contact_form_submission_spam(self):
        """Test soumission avec spam détecté"""
        response = self.client.post(reverse('accueil:contact'), {
            'nom': 'Spam Bot',
            'email': 'spam@bot.com',
            'sujet': 'devis',
            'message': 'Spam message',
            'website': 'http://spam.com'  # honeypot rempli
        })

        # Ne doit pas rediriger, reste sur la page avec erreurs
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Spam détecté')

        # Aucun email ne doit être envoyé
        self.assertEqual(len(mail.outbox), 0)

    def test_contact_breadcrumb_navigation(self):
        """Test du fil d'ariane"""
        response = self.client.get(reverse('accueil:contact'))

        self.assertContains(response, 'Accueil')
        self.assertContains(response, 'CONTACT')
        self.assertContains(response, 'breadcrumb')

    def test_contact_form_csrf_protection(self):
        """Test protection CSRF"""
        response = self.client.get(reverse('accueil:contact'))

        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')
