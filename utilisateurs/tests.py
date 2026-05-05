
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import ProfilClient, ProfilPhotographe, Utilisateur


class UtilisateurModelTest(TestCase):
    """Tests pour le modèle Utilisateur"""

    def setUp(self) -> None:
        """Configuration des tests"""
        self.photographe_data = {
            'username': 'photographe_test',
            'email': 'photo@test.com',
            'role': Utilisateur.Role.PHOTOGRAPHE
        }
        self.client_data = {
            'username': 'client_test',
            'email': 'client@test.com',
            'role': Utilisateur.Role.CLIENT
        }

    def test_creation_utilisateur_photographe(self) -> None:
        """Test création d'un utilisateur photographe"""
        photographe = Utilisateur.objects.create_user(**self.photographe_data)

        self.assertTrue(photographe.est_photographe())
        self.assertFalse(photographe.est_client())
        self.assertFalse(photographe.est_visiteur())

    def test_creation_utilisateur_client(self) -> None:
        """Test création d'un utilisateur client"""
        client = Utilisateur.objects.create_user(**self.client_data)

        self.assertFalse(client.est_photographe())
        self.assertTrue(client.est_client())
        self.assertFalse(client.est_visiteur())

    def test_utilisateur_visiteur_par_defaut(self) -> None:
        """Test que le rôle par défaut est visiteur"""
        visiteur = Utilisateur.objects.create_user(
            username='visiteur_test',
            email='visiteur@test.com'
        )

        self.assertFalse(visiteur.est_photographe())
        self.assertFalse(visiteur.est_client())
        self.assertTrue(visiteur.est_visiteur())
        self.assertEqual(visiteur.role, Utilisateur.Role.VISITEUR)

    def test_un_seul_photographe_autorise(self) -> None:
        """Test qu'un seul photographe peut exister"""
        # Créer le premier photographe
        Utilisateur.objects.create_user(**self.photographe_data)

        # Essayer de créer un second photographe
        with self.assertRaises(ValidationError) as context:
            second_photographe = Utilisateur(
                username='photographe_2',
                email='photo2@test.com',
                role=Utilisateur.Role.PHOTOGRAPHE
            )
            second_photographe.save()

        self.assertIn("Un seul photographe est autorisé", str(context.exception))

    def test_modifier_role_en_photographe_impossible(self) -> None:
        """Test qu'on ne peut pas changer un utilisateur en photographe si un existe déjà"""
        # Créer un photographe
        Utilisateur.objects.create_user(**self.photographe_data)

        # Créer un client
        client = Utilisateur.objects.create_user(**self.client_data)

        # Essayer de changer le client en photographe
        with self.assertRaises(ValidationError):
            client.role = Utilisateur.Role.PHOTOGRAPHE
            client.save()

    def test_peut_creer_plusieurs_clients(self) -> None:
        """Test qu'on peut créer plusieurs clients"""
        client1 = Utilisateur.objects.create_user(
            username='client1',
            email='client1@test.com',
            role=Utilisateur.Role.CLIENT
        )
        client2 = Utilisateur.objects.create_user(
            username='client2',
            email='client2@test.com',
            role=Utilisateur.Role.CLIENT
        )

        self.assertEqual(Utilisateur.objects.filter(role=Utilisateur.Role.CLIENT).count(), 2)
        self.assertTrue(client1.est_client())
        self.assertTrue(client2.est_client())


class ProfilCreationSignalTest(TestCase):
    """Tests pour la création automatique des profils"""

    def test_profil_photographe_cree_automatiquement(self) -> None:
        """Test que le profil photographe est créé automatiquement"""
        photographe = Utilisateur.objects.create_user(
            username='photographe',
            email='photo@test.com',
            first_name='Jean',
            last_name='Dupont',
            role=Utilisateur.Role.PHOTOGRAPHE
        )

        # Vérifier que le profil photographe a été créé
        self.assertTrue(hasattr(photographe, 'profil_photographe'))
        self.assertEqual(photographe.profil_photographe.nom_entreprise, 'Studio Jean Dupont')

    def test_profil_client_cree_automatiquement(self) -> None:
        """Test que le profil client est créé automatiquement"""
        client = Utilisateur.objects.create_user(
            username='client',
            email='client@test.com',
            role=Utilisateur.Role.CLIENT
        )

        # Vérifier que le profil client a été créé
        self.assertTrue(hasattr(client, 'profil_client'))
        self.assertIsInstance(client.profil_client, ProfilClient)

    def test_visiteur_pas_de_profil_automatique(self) -> None:
        """Test qu'aucun profil n'est créé pour les visiteurs"""
        visiteur = Utilisateur.objects.create_user(
            username='visiteur',
            email='visiteur@test.com'
            # role par défaut = VISITEUR
        )

        # Vérifier qu'aucun profil n'a été créé
        self.assertFalse(hasattr(visiteur, 'profil_photographe'))
        self.assertFalse(hasattr(visiteur, 'profil_client'))


class ProfilModelTest(TestCase):
    """Tests pour les modèles de profils"""

    def test_profil_photographe_str(self) -> None:
        """Test de la représentation string du profil photographe"""
        photographe = Utilisateur.objects.create_user(
            username='photographe',
            role=Utilisateur.Role.PHOTOGRAPHE
        )
        profil = ProfilPhotographe.objects.get(utilisateur=photographe)
        profil.nom_entreprise = "Studio Test"
        profil.save()

        self.assertEqual(str(profil), "Profil photographe: Studio Test")

    def test_profil_client_str(self) -> None:
        """Test de la représentation string du profil client"""
        client = Utilisateur.objects.create_user(
            username='client_test',
            first_name='Marie',
            last_name='Martin',
            role=Utilisateur.Role.CLIENT
        )
        profil = ProfilClient.objects.get(utilisateur=client)

        self.assertEqual(str(profil), "Profil client: Marie Martin")
