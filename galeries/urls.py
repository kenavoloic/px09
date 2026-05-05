from django.urls import path

from . import views

app_name = 'galeries'

urlpatterns = [
    path('galerie/<slug:galerie_slug>/', views.galerie_detail, name='galerie_detail'),
    path('galerie/<slug:galerie_slug>/<slug:collection_slug>/', views.collection_detail, name='collection_detail'),
    path('photo/<int:photo_id>/', views.photo_detail, name='photo_detail'),
]
