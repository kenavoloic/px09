from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from commandes.models import Client as ClientCommande
from commandes.models import Commande, PhotoCommande
from galeries.models import Galerie, Photo, PhotoVersion


class ClientModelTest(TestCase):
    """Tests pour le modèle Client"""

    def test_creation_client(self):
        """Test de création d'un client"""
        client = ClientCommande.objects.create(
            prenom="Jean",
            nom="Dupont",
            email="jean.dupont@example.com",
            telephone="0123456789",
            entreprise="ACME Corp",
            adresse="123 rue de la Test"
        )

        self.assertEqual(client.prenom, "Jean")
        self.assertEqual(client.nom, "Dupont")
        self.assertEqual(client.email, "jean.dupont@example.com")

    def test_str_representation_avec_entreprise(self):
        """Test de la représentation string avec entreprise"""
        client = ClientCommande.objects.create(
            prenom="Jean",
            nom="Dupont",
            email="jean.dupont@example.com",
            entreprise="ACME Corp"
        )

        self.assertEqual(str(client), "Dupont Jean (ACME Corp)")

    def test_str_representation_sans_entreprise(self):
        """Test de la représentation string sans entreprise"""
        client = ClientCommande.objects.create(
            prenom="Jean",
            nom="Dupont",
            email="jean.dupont@example.com"
        )

        self.assertEqual(str(client), "Dupont Jean")

    def test_get_nom_complet(self):
        """Test de la méthode get_nom_complet"""
        client = ClientCommande.objects.create(
            prenom="Marie",
            nom="Martin",
            email="marie.martin@example.com"
        )

        self.assertEqual(client.get_nom_complet(), "Marie Martin")

    def test_email_unique(self):
        """Test de l'unicité de l'email"""
        ClientCommande.objects.create(
            prenom="Jean",
            nom="Dupont",
            email="test@example.com"
        )

        with self.assertRaises(Exception):
            ClientCommande.objects.create(
                prenom="Marie",
                nom="Martin",
                email="test@example.com"
            )


class CommandeModelTest(TestCase):
    """Tests pour le modèle Commande"""

    def setUp(self):
        self.client = ClientCommande.objects.create(
            prenom="Jean",
            nom="Dupont",
            email="jean.dupont@example.com"
        )
        self.expire_le = timezone.now() + timedelta(days=30)

    def test_creation_commande(self):
        """Test de création d'une commande"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Commande Test",
            description="Description test",
            expire_le=self.expire_le
        )

        self.assertEqual(commande.client, self.client)
        self.assertEqual(commande.titre, "Commande Test")
        self.assertEqual(commande.statut, 'en_preparation')
        self.assertTrue(commande.code_acces)
        self.assertTrue(commande.reference)

    def test_génération_code_accès_unique(self):
        """Test de génération d'un code d'accès unique"""
        commande1 = Commande.objects.create(
            client=self.client,
            titre="Commande 1",
            expire_le=self.expire_le
        )
        commande2 = Commande.objects.create(
            client=self.client,
            titre="Commande 2",
            expire_le=self.expire_le
        )

        self.assertNotEqual(commande1.code_acces, commande2.code_acces)
        self.assertTrue(len(commande1.code_acces) > 10)

    def test_génération_référence_unique(self):
        """Test de génération d'une référence unique"""
        commande1 = Commande.objects.create(
            client=self.client,
            titre="Commande 1",
            expire_le=self.expire_le
        )
        commande2 = Commande.objects.create(
            client=self.client,
            titre="Commande 2",
            expire_le=self.expire_le
        )

        self.assertNotEqual(commande1.reference, commande2.reference)
        self.assertRegex(commande1.reference, r'\d{4}_\d{2}_\d{2}_\d{4}')

    def test_est_accessible_commande_livrée_non_expirée(self):
        """Test qu'une commande livrée et non expirée est accessible"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Commande Test",
            statut='livree',
            expire_le=timezone.now() + timedelta(days=1)
        )

        self.assertTrue(commande.est_accessible())

    def test_est_accessible_commande_en_préparation(self):
        """Test qu'une commande en préparation n'est pas accessible"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Commande Test",
            statut='en_preparation',
            expire_le=timezone.now() + timedelta(days=1)
        )

        self.assertFalse(commande.est_accessible())

    def test_est_accessible_commande_expirée(self):
        """Test qu'une commande expirée n'est pas accessible"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Commande Test",
            statut='livree',
            expire_le=timezone.now() - timedelta(days=1)
        )

        self.assertFalse(commande.est_accessible())

    def test_est_expiree(self):
        """Test de la méthode est_expiree"""
        # Commande non expirée
        commande_valide = Commande.objects.create(
            client=self.client,
            titre="Valide",
            expire_le=timezone.now() + timedelta(days=1)
        )

        # Commande expirée
        commande_expiree = Commande.objects.create(
            client=self.client,
            titre="Expirée",
            expire_le=timezone.now() - timedelta(days=1)
        )

        self.assertFalse(commande_valide.est_expiree())
        self.assertTrue(commande_expiree.est_expiree())

    def test_enregistrer_visite(self):
        """Test d'enregistrement d'une visite"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Test",
            expire_le=self.expire_le
        )

        self.assertEqual(commande.nombre_vues, 0)
        self.assertIsNone(commande.premiere_visite_le)

        commande.enregistrer_visite()

        self.assertEqual(commande.nombre_vues, 1)
        self.assertIsNotNone(commande.premiere_visite_le)
        self.assertIsNotNone(commande.derniere_visite_le)

    def test_enregistrer_telechargement(self):
        """Test d'enregistrement d'un téléchargement"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Test",
            expire_le=self.expire_le
        )

        self.assertEqual(commande.nombre_telechargements, 0)

        commande.enregistrer_telechargement()

        self.assertEqual(commande.nombre_telechargements, 1)

    def test_str_representation(self):
        """Test de la représentation string"""
        commande = Commande.objects.create(
            client=self.client,
            titre="Ma Commande",
            expire_le=self.expire_le
        )

        expected = f"{commande.reference} - Ma Commande"
        self.assertEqual(str(commande), expected)


class PhotoCommandeModelTest(TestCase):
    """Tests pour le modèle PhotoCommande"""

    def setUp(self):
        self.client = ClientCommande.objects.create(
            prenom="Test",
            nom="User",
            email="test@example.com"
        )

        self.commande = Commande.objects.create(
            client=self.client,
            titre="Test Commande",
            expire_le=timezone.now() + timedelta(days=30)
        )

        self.galerie = Galerie.objects.create(
            nom="Test Galerie",
            slug="test",
            description="Test"
        )

        self.photo = Photo.objects.create(
            galerie=self.galerie,
            titre="Test Photo",
            nom_fichier="test.jpg",
            largeur_originale=1920,
            hauteur_originale=1080
        )

        self.version = PhotoVersion.objects.create(
            photo=self.photo,
            traitement="couleur",
            largeur=1920,
            hauteur=1080
        )

    def test_creation_photo_commande(self):
        """Test de création d'une photo de commande"""
        photo_commande = PhotoCommande.objects.create(
            commande=self.commande,
            photo_originale=self.photo,
            version_selectionnee=self.version,
            titre_personnalise="Titre perso"
        )

        self.assertEqual(photo_commande.commande, self.commande)
        self.assertEqual(photo_commande.photo_originale, self.photo)
        self.assertEqual(photo_commande.titre_personnalise, "Titre perso")

    def test_get_titre_affichage_avec_titre_personnalise(self):
        """Test d'affichage du titre personnalisé"""
        photo_commande = PhotoCommande.objects.create(
            commande=self.commande,
            photo_originale=self.photo,
            version_selectionnee=self.version,
            titre_personnalise="Titre Custom"
        )

        self.assertEqual(photo_commande.get_titre_affichage(), "Titre Custom")

    def test_get_titre_affichage_sans_titre_personnalise(self):
        """Test d'affichage du titre de la photo originale"""
        photo_commande = PhotoCommande.objects.create(
            commande=self.commande,
            photo_originale=self.photo,
            version_selectionnee=self.version
        )

        self.assertEqual(photo_commande.get_titre_affichage(), self.photo.get_titre_affichage())

    def test_contrainte_unicité(self):
        """Test de la contrainte d'unicité"""
        PhotoCommande.objects.create(
            commande=self.commande,
            photo_originale=self.photo,
            version_selectionnee=self.version
        )

        with self.assertRaises(Exception):
            PhotoCommande.objects.create(
                commande=self.commande,
                photo_originale=self.photo,
                version_selectionnee=self.version
            )


class CommandeViewsTest(TestCase):
    """Tests pour les vues de l'application commandes"""

    def setUp(self):
        self.client_http = Client()

        self.client_commande = ClientCommande.objects.create(
            prenom="Test",
            nom="User",
            email="test@example.com"
        )

        self.commande = Commande.objects.create(
            client=self.client_commande,
            titre="Test Commande",
            statut='livree',
            expire_le=timezone.now() + timedelta(days=30)
        )

        self.galerie = Galerie.objects.create(
            nom="Test Galerie",
            slug="test",
            description="Test"
        )

        self.photo = Photo.objects.create(
            galerie=self.galerie,
            titre="Test Photo",
            nom_fichier="test.jpg",
            largeur_originale=1920,
            hauteur_originale=1080
        )

        self.version = PhotoVersion.objects.create(
            photo=self.photo,
            traitement="couleur",
            largeur=1920,
            hauteur=1080
        )

        self.photo_commande = PhotoCommande.objects.create(
            commande=self.commande,
            photo_originale=self.photo,
            version_selectionnee=self.version
        )

    def test_acces_commande_valide(self):
        """Test d'accès à une commande valide"""
        url = reverse('commandes:acces_commande', kwargs={'code_acces': self.commande.code_acces})
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.commande.titre)
        self.assertIn('commande', response.context)
        self.assertIn('photos', response.context)

    def test_acces_commande_code_invalide(self):
        """Test d'accès avec un code invalide"""
        url = reverse('commandes:acces_commande', kwargs={'code_acces': 'code-invalide'})
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 404)

    def test_acces_commande_expiree(self):
        """Test d'accès à une commande expirée"""
        commande_expiree = Commande.objects.create(
            client=self.client_commande,
            titre="Expirée",
            statut='livree',
            expire_le=timezone.now() - timedelta(days=1)
        )

        url = reverse('commandes:acces_commande', kwargs={'code_acces': commande_expiree.code_acces})
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expirée")

    def test_acces_commande_en_preparation(self):
        """Test d'accès à une commande en préparation"""
        commande_prep = Commande.objects.create(
            client=self.client_commande,
            titre="En préparation",
            statut='en_preparation',
            expire_le=timezone.now() + timedelta(days=30)
        )

        url = reverse('commandes:acces_commande', kwargs={'code_acces': commande_prep.code_acces})
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "non disponible")

    def test_photo_detail_commande(self):
        """Test de la vue détail photo"""
        url = reverse('commandes:photo_detail_commande', kwargs={
            'code_acces': self.commande.code_acces,
            'photo_id': self.photo_commande.id
        })
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('photo', response.context)
        self.assertEqual(response.context['photo'], self.photo_commande)

    def test_photo_detail_commande_non_accessible(self):
        """Test détail photo pour commande non accessible"""
        commande_prep = Commande.objects.create(
            client=self.client_commande,
            titre="En préparation",
            statut='en_preparation',
            expire_le=timezone.now() + timedelta(days=30)
        )

        photo_commande = PhotoCommande.objects.create(
            commande=commande_prep,
            photo_originale=self.photo,
            version_selectionnee=self.version
        )

        url = reverse('commandes:photo_detail_commande', kwargs={
            'code_acces': commande_prep.code_acces,
            'photo_id': photo_commande.id
        })

        response = self.client_http.get(url)
        # La vue retourne 403 Forbidden pour une commande non accessible
        self.assertEqual(response.status_code, 403)

    def test_telecharger_photo_web_pas_de_fichier(self):
        """Test de téléchargement photo sans fichier web"""
        url = reverse('commandes:telecharger_photo', kwargs={
            'code_acces': self.commande.code_acces,
            'photo_id': self.photo_commande.id
        })

        response = self.client_http.post(url, {'type': 'web'})

        # Sans fichier, doit rediriger vers la commande
        self.assertEqual(response.status_code, 302)

    def test_aide_commande(self):
        """Test de la page d'aide"""
        url = reverse('commandes:aide_commande', kwargs={'code_acces': self.commande.code_acces})
        response = self.client_http.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('commande', response.context)
