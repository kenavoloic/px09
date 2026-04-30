"""
Production settings for Django project.
"""

import os
from typing import Any

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG: bool = False

ALLOWED_HOSTS: list[str] = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Production security settings
SECURE_SSL_REDIRECT: bool = True
SECURE_HSTS_SECONDS: int = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
SECURE_HSTS_PRELOAD: bool = True
SECURE_PROXY_SSL_HEADER: tuple[str, str] = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE: bool = True
CSRF_COOKIE_SECURE: bool = True

# Static files configuration with WhiteNoise
STATICFILES_STORAGE: str = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Email configuration
EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: str | None = os.environ.get("EMAIL_HOST")
EMAIL_PORT: int = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER: str | None = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD: str | None = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS: bool = True

# Logging configuration
LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
