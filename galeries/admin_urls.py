"""
URLs pour les vues d'administration personnalisées
"""
from django.urls import path

from .admin_views import upload_photos_view
from .admin_views_photos import (
    ajax_collections,
    photo_ordering_view,
    photo_thumbnail_api,
    update_photo_order,
)

app_name = 'galeries_admin'

urlpatterns = [
    path('upload/', upload_photos_view, name='upload_photos'),
    path('photo-ordering/', photo_ordering_view, name='photo_ordering'),
    path('api/update-photo-order/', update_photo_order, name='update_photo_order'),
    path('api/collections/', ajax_collections, name='ajax_collections'),
    path('api/photo/<int:photo_id>/thumbnail/', photo_thumbnail_api, name='photo_thumbnail'),
]
