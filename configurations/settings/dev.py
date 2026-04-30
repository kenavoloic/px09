"""
Development settings for Django project.
"""

from typing import Any

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG: bool = True

ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

# Development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",
]

# Development middleware
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Database for development (SQLite for simplicity)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Debug toolbar configuration
INTERNAL_IPS: list[str] = [
    "127.0.0.1",
]

# Email backend for development
EMAIL_BACKEND: str = "django.core.mail.backends.console.EmailBackend"

# Logging configuration
LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
