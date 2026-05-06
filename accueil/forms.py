"""
Formulaires pour l'application accueil
"""
from django import forms
from django.conf import settings
from django.core.mail import send_mail


class ContactForm(forms.Form):
    """Formulaire de contact pour les visiteurs"""

    SUJET_CHOICES = [
        ('devis', 'Demande de devis'),
        ('info', 'Demande d\'information'),
        ('rdv', 'Prise de rendez-vous'),
        ('autre', 'Autre'),
    ]

    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre nom'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.com'
        })
    )

    sujet = forms.ChoiceField(
        choices=SUJET_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    message = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Votre message...',
            'rows': 5
        })
    )

    # Honeypot anti-spam (invisible)
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none!important',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )

    def clean_website(self) -> str:
        """Vérification honeypot anti-spam"""
        website = self.cleaned_data.get('website', '')
        if website:
            raise forms.ValidationError('Spam détecté.')
        return website

    def send_email(self) -> bool:
        """Envoie l'email de contact au photographe"""
        if not self.is_valid():
            return False

        data = self.cleaned_data

        # Email au photographe
        subject_photographer = f"[Portfolio] {data['sujet']} - {data['nom']}"
        message_photographer = f"""
Nouvelle demande de contact via le portfolio :

Nom : {data['nom']}
Email : {data['email']}
Sujet : {dict(self.SUJET_CHOICES)[data['sujet']]}

Message :
{data['message']}

---
Envoyé automatiquement depuis le site Hors les Murs
        """.strip()

        # Email de confirmation au visiteur
        subject_visitor = "Votre message a bien été envoyé - Hors les Murs"
        message_visitor = f"""
Bonjour {data['nom']},

Votre message a bien été envoyé et je vous en remercie.

Je vous répondrai dans les plus brefs délais, généralement sous 24-48h.

Objet de votre demande : {dict(self.SUJET_CHOICES)[data['sujet']]}

Cordialement,
Hors les Murs - Studio photographique

---
Ceci est un email automatique, merci de ne pas y répondre.
        """.strip()

        try:
            # Envoi au photographe
            send_mail(
                subject=subject_photographer,
                message=message_photographer,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )

            # Envoi de confirmation au visiteur
            send_mail(
                subject=subject_visitor,
                message=message_visitor,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[data['email']],
                fail_silently=False,
            )

            return True

        except Exception:
            return False
