"""
Tests basiques pour les modèles utilisateurs
"""

from django.test import TestCase

from utilisateurs.models import Utilisateur


class TestUtilisateurBasic(TestCase):
    """Tests basiques pour Utilisateur"""

    def test_creation_utilisateur(self):
        """Test de création d'un utilisateur"""
        user = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="motdepasse123",
            role=Utilisateur.Role.VISITEUR,
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, Utilisateur.Role.VISITEUR)
        self.assertTrue(user.check_password("motdepasse123"))

    def test_roles_disponibles(self):
        """Test des rôles disponibles"""
        self.assertEqual(Utilisateur.Role.PHOTOGRAPHE, "photographe")
        self.assertEqual(Utilisateur.Role.CLIENT, "client")
        self.assertEqual(Utilisateur.Role.VISITEUR, "visiteur")

    def test_methodes_role(self):
        """Test des méthodes de vérification de rôle"""
        photographe = Utilisateur(role=Utilisateur.Role.PHOTOGRAPHE)
        client = Utilisateur(role=Utilisateur.Role.CLIENT)
        visiteur = Utilisateur(role=Utilisateur.Role.VISITEUR)

        # Test est_photographe
        self.assertTrue(photographe.est_photographe())
        self.assertFalse(client.est_photographe())
        self.assertFalse(visiteur.est_photographe())

        # Test est_client
        self.assertFalse(photographe.est_client())
        self.assertTrue(client.est_client())
        self.assertFalse(visiteur.est_client())

        # Test est_visiteur
        self.assertFalse(photographe.est_visiteur())
        self.assertFalse(client.est_visiteur())
        self.assertTrue(visiteur.est_visiteur())

    def test_default_role(self):
        """Test du rôle par défaut"""
        user = Utilisateur.objects.create_user(
            username="test", email="test@example.com", password="pass"
        )
        self.assertEqual(user.role, Utilisateur.Role.VISITEUR)

    def test_cree_le_auto_now_add(self):
        """Test que cree_le est défini automatiquement"""
        user = Utilisateur.objects.create_user(
            username="test", email="test@example.com", password="pass"
        )
        self.assertIsNotNone(user.cree_le)
