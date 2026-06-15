"""
URL configuration for Django project.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(f"{settings.ADMIN_URL}/galeries/", include("galeries.admin_urls")),
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("", include("accueil.urls")),
    path("", include("galeries.urls")),
    path("commande/", include("commandes.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = (
        [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
        + urlpatterns
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )
