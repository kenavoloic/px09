"""
Commande de test de la configuration email du formulaire de contact
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accueil.forms import ContactForm


class Command(BaseCommand):
    help = 'Test la configuration email du formulaire de contact'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-real-email',
            action='store_true',
            help='Envoie un vrai email de test (sinon simule)',
        )
        parser.add_argument(
            '--to-email',
            type=str,
            help='Email de destination pour le test',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Test de configuration email du contact ===')
        )
        
        # Vérification de la configuration
        self.stdout.write('\n1. Configuration email actuelle:')
        self.stdout.write(f'   - EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   - DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'   - CONTACT_EMAIL: {settings.CONTACT_EMAIL}')
        
        # Test du formulaire
        self.stdout.write('\n2. Test de validation du formulaire:')
        test_email = options.get('to_email') or 'admin@example.com'
        form_data = {
            'nom': 'Test Administrateur',
            'email': test_email,
            'sujet': 'info',
            'message': 'Test automatique de configuration email depuis la commande de gestion.',
            'website': '',  # Honeypot vide
        }
        
        form = ContactForm(data=form_data)
        if form.is_valid():
            self.stdout.write(self.style.SUCCESS('   ✅ Formulaire valide'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Formulaire invalide'))
            for field, errors in form.errors.items():
                self.stdout.write(f'      {field}: {errors}')
            return
        
        # Test d'envoi
        self.stdout.write('\n3. Test d\'envoi d\'email:')
        
        if options['send_real_email']:
            self.stdout.write('   Mode: ENVOI RÉEL')
            try:
                success = form.send_email()
                if success:
                    self.stdout.write(self.style.SUCCESS('   ✅ Email envoyé avec succès'))
                else:
                    self.stdout.write(self.style.ERROR('   ❌ Échec de l\'envoi'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erreur: {e}'))
        else:
            self.stdout.write('   Mode: SIMULATION (ajoutez --send-real-email pour un vrai envoi)')
            self.stdout.write('   ℹ️  Le formulaire utilise le backend: console en développement')
        
        # Conseils de configuration
        self.stdout.write('\n4. Configuration pour la production:')
        if 'console' in settings.EMAIL_BACKEND.lower():
            self.stdout.write(self.style.WARNING('   ⚠️  Backend console actif (développement)'))
            self.stdout.write('   Pour la production, configurez:')
            self.stdout.write('   - EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"')
            self.stdout.write('   - EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, etc.')
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Backend SMTP configuré'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Test terminé'))