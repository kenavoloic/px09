"""
Tests basiques pour les modèles galeries
"""

from django.test import TestCase

from galeries.models import Collection, Galerie, Photo


class TestGalerieBasic(TestCase):
    """Tests basiques pour Galerie"""

    def test_creation_galerie(self):
        """Test de création d'une galerie"""
        galerie = Galerie.objects.create(
            nom="Test Galerie",
            slug="test-galerie",
            description="Description de test",
            ordre_affichage=1,
            est_publique=True,
        )

        self.assertEqual(galerie.nom, "Test Galerie")
        self.assertEqual(galerie.slug, "test-galerie")
        self.assertTrue(galerie.est_publique)

    def test_str_galerie(self):
        """Test de la représentation string"""
        galerie = Galerie.objects.create(nom="Ma Galerie", slug="ma-galerie")
        self.assertEqual(str(galerie), "Ma Galerie")

    def test_get_absolute_url(self):
        """Test de l'URL absolue"""
        galerie = Galerie.objects.create(nom="Test", slug="test-galerie")
        self.assertEqual(galerie.get_absolute_url(), "/galerie/test-galerie/")


class TestCollectionBasic(TestCase):
    """Tests basiques pour Collection"""

    def test_creation_collection(self):
        """Test de création d'une collection"""
        galerie = Galerie.objects.create(nom="Galerie", slug="galerie")
        collection = Collection.objects.create(
            galerie=galerie,
            nom="Test Collection",
            slug="test-collection",
            ordre_affichage=1,
            est_publique=True,
        )

        self.assertEqual(collection.nom, "Test Collection")
        self.assertEqual(collection.galerie, galerie)

    def test_str_collection(self):
        """Test de la représentation string"""
        galerie = Galerie.objects.create(nom="Galerie", slug="galerie")
        collection = Collection.objects.create(
            galerie=galerie, nom="Ma Collection", slug="ma-collection"
        )
        self.assertEqual(str(collection), "Galerie - Ma Collection")


class TestPhotoBasic(TestCase):
    """Tests basiques pour Photo"""

    def test_creation_photo(self):
        """Test de création d'une photo"""
        galerie = Galerie.objects.create(nom="Galerie", slug="galerie")
        photo = Photo.objects.create(
            galerie=galerie,
            titre="Test Photo",
            ordre_affichage=1,
            est_publique=True,
            largeur_originale=1920,
            hauteur_originale=1080,
        )

        self.assertEqual(photo.titre, "Test Photo")
        self.assertEqual(photo.galerie, galerie)

    def test_str_photo_avec_titre(self):
        """Test de la représentation string avec titre"""
        galerie = Galerie.objects.create(nom="Galerie", slug="galerie")
        photo = Photo.objects.create(
            galerie=galerie,
            titre="Ma Photo",
            largeur_originale=1920,
            hauteur_originale=1080,
        )
        self.assertEqual(str(photo), "Ma Photo")

    def test_str_photo_sans_titre(self):
        """Test de la représentation string sans titre"""
        galerie = Galerie.objects.create(nom="Galerie", slug="galerie")
        photo = Photo.objects.create(
            galerie=galerie, largeur_originale=1920, hauteur_originale=1080
        )
        # Par défaut, la configuration retourne "Sans titre" pour les photos sans titre personnalisé
        self.assertEqual(str(photo), "Sans titre")
