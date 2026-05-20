from django.urls import path

from . import views

app_name = 'galeries'

urlpatterns = [
    # Galeries privées (AVANT les publiques pour éviter les conflits)
    path('galerie/prive/<slug:galerie_slug>/', views.galerie_privee, name='galerie_privee'),
    path('galerie/prive/<slug:galerie_slug>/<slug:collection_slug>/', views.collection_privee, name='collection_privee'),
    path('photo/prive/<int:photo_id>/', views.photo_privee, name='photo_privee'),
    path('deconnexion-privee/', views.deconnexion_privee, name='deconnexion_privee'),
    
    # Galeries publiques
    path('galerie/<slug:galerie_slug>/', views.galerie_detail, name='galerie_detail'),
    path('galerie/<slug:galerie_slug>/<slug:collection_slug>/', views.collection_detail, name='collection_detail'),
    path('photo/<int:photo_id>/', views.photo_detail, name='photo_detail'),
]
