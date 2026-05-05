"""
URL configuration for Django project.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("", include("accueil.urls")),
    path("", include("galeries.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
