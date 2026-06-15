"""
Test Django settings configuration.
"""

from django.apps import apps
from django.conf import settings
from django.test import TestCase


class SettingsTest(TestCase):
    """Test Django settings configuration."""

    def test_secret_key_exists(self):
        """Test that SECRET_KEY is configured."""
        self.assertTrue(hasattr(settings, "SECRET_KEY"))
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, "")

    def test_debug_setting(self):
        """Test DEBUG setting based on environment."""
        # This will be True in dev, False in prod
        self.assertIsInstance(settings.DEBUG, bool)

    def test_installed_apps(self):
        """Test that required apps are installed."""
        required_apps = [
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ]
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

        # L'admin est fourni via une AppConfig personnalisée (CustomAdminSite),
        # donc on vérifie son installation plutôt que sa présence littérale.
        self.assertTrue(apps.is_installed("django.contrib.admin"))

    def test_middleware_configuration(self):
        """Test that required middleware is configured."""
        required_middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ]
        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)

    def test_database_configuration(self):
        """Test that database is configured."""
        self.assertIn("default", settings.DATABASES)
        self.assertIn("ENGINE", settings.DATABASES["default"])
        self.assertIn("NAME", settings.DATABASES["default"])
