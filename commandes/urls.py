from django.urls import path

from . import views

app_name = 'commandes'

urlpatterns = [
    # Accès principal à une commande
    path('acces/<str:code_acces>/', views.acces_commande, name='acces_commande'),
    
    # Vue détaillée d'une photo dans la commande
    path('acces/<str:code_acces>/photo/<int:photo_id>/', views.photo_detail_commande, name='photo_detail_commande'),
    
    # Téléchargement d'une photo individuelle
    path('acces/<str:code_acces>/photo/<int:photo_id>/telecharger/', views.telecharger_photo, name='telecharger_photo'),
    
    # Téléchargement de toutes les photos en ZIP
    path('acces/<str:code_acces>/telecharger-tout/', views.telecharger_toutes_photos, name='telecharger_toutes_photos'),
    
    # Page d'aide
    path('acces/<str:code_acces>/aide/', views.aide_commande, name='aide_commande'),
]