from django.urls import path

from . import views

app_name = 'galeries'

urlpatterns = [
    # Galeries privées (AVANT les publiques pour éviter les conflits)
    path('galeries-privees/', views.tableau_bord_prive, name='tableau_bord_prive'),
    path('galerie/prive/<slug:galerie_slug>/telecharger-zip/', views.telecharger_galerie_zip, name='telecharger_galerie_zip'),
    path('galerie/prive/<slug:galerie_slug>/', views.galerie_privee, name='galerie_privee'),
    path('galerie/prive/<slug:galerie_slug>/<slug:collection_slug>/', views.collection_privee, name='collection_privee'),
    path('photo/prive/<int:photo_id>/', views.photo_privee, name='photo_privee'),
    path('deconnexion-privee/', views.deconnexion_privee, name='deconnexion_privee'),

    # Galeries publiques
    path('galerie/<slug:galerie_slug>/', views.galerie_detail, name='galerie_detail'),
    path('galerie/<slug:galerie_slug>/<slug:collection_slug>/', views.collection_detail, name='collection_detail'),
    path('photo/<int:photo_id>/', views.photo_detail, name='photo_detail'),
]
