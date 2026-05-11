# -*- coding: utf-8 -*-
from typing import Any, Optional, Dict
from django.contrib import admin
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from .models import AccueilConfig, SectionAccueil


class AccueilConfigForm(ModelForm):
    """Formulaire personnalisé pour la configuration d'accueil"""
    
    class Meta:
        model = AccueilConfig
        fields = '__all__'
    
    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        return cleaned_data or {}


@admin.register(AccueilConfig)
class AccueilConfigAdmin(admin.ModelAdmin):
    form = AccueilConfigForm
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return not AccueilConfig.objects.exists()
    
    def has_delete_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        return False
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre_site', 'sous_titre', 'description', 'hero_image')
        }),
        ('Sections de la page', {
            'fields': ('titre_galeries', 'titre_acces_prive', 'description_acces_prive')
        }),
        ('Modal d\'accès privé', {
            'fields': ('modal_titre', 'modal_sous_titre', 'modal_placeholder_code'),
            'classes': ('collapse',)
        }),
        ('Informations', {
            'fields': ('cree_le', 'modifie_le'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('cree_le', 'modifie_le')
    
    def get_object(self, request: HttpRequest, object_id: str, from_field: Optional[str] = None) -> AccueilConfig:
        return AccueilConfig.get_config()
    
    def changelist_view(self, request: HttpRequest, extra_context: Optional[Dict[str, Any]] = None) -> Any:
        config = AccueilConfig.get_config()
        return self.changeform_view(request, str(config.pk))


@admin.register(SectionAccueil)
class SectionAccueilAdmin(admin.ModelAdmin):
    list_display = ['titre', 'position', 'ordre', 'est_active', 'modifie_le']
    list_filter = ['position', 'est_active', 'cree_le']
    search_fields = ['titre', 'contenu']
    list_editable = ['ordre', 'est_active']
    
    fieldsets = (
        (None, {
            'fields': ('titre', 'contenu', 'position', 'ordre', 'est_active')
        }),
        ('Informations', {
            'fields': ('cree_le', 'modifie_le'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('cree_le', 'modifie_le')