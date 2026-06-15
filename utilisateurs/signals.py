from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProfilClient, ProfilPhotographe, Utilisateur


@receiver(post_save, sender=Utilisateur)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """
    Crée automatiquement le profil approprié selon le rôle de l'utilisateur.
    """
    if created:
        if instance.role == Utilisateur.Role.PHOTOGRAPHE:
            ProfilPhotographe.objects.create(
                utilisateur=instance,
                nom_entreprise=f"Studio {instance.get_full_name() or instance.username}",
            )
        elif instance.role == Utilisateur.Role.CLIENT:
            ProfilClient.objects.create(utilisateur=instance)


@receiver(post_save, sender=Utilisateur)
def synchroniser_profil_utilisateur(sender, instance, created, **kwargs):
    """
    Synchronise les profils quand le rôle d'un utilisateur change.
    """
    if not created:  # Seulement pour les mises à jour
        # Vérifier si l'utilisateur doit avoir un profil photographe
        if instance.role == Utilisateur.Role.PHOTOGRAPHE:
            if (
                not hasattr(instance, "profil_photographe")
                or not instance.profil_photographe
            ):
                ProfilPhotographe.objects.get_or_create(
                    utilisateur=instance,
                    defaults={
                        "nom_entreprise": f"Studio {instance.get_full_name() or instance.username}"
                    },
                )

        # Vérifier si l'utilisateur doit avoir un profil client
        if instance.role == Utilisateur.Role.CLIENT:
            if not hasattr(instance, "profil_client") or not instance.profil_client:
                ProfilClient.objects.get_or_create(utilisateur=instance)
