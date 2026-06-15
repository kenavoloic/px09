"""
Proxy models pour créer des sections visibles dans l'admin
"""

from django.contrib import admin

from .models import Photo


class PhotoUploadProxy(Photo):
    """Proxy pour Upload de photos"""

    class Meta:
        proxy = True
        verbose_name = "📷 Upload de photos"
        verbose_name_plural = "📷 Upload de photos"


class PhotoOrderingProxy(Photo):
    """Proxy pour Gestion de l'ordre"""

    class Meta:
        proxy = True
        verbose_name = "🔄 Ordre des photos"
        verbose_name_plural = "🔄 Ordre des photos"


@admin.register(PhotoUploadProxy)
class PhotoUploadAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        return redirect("/admin/galeries/upload/")


@admin.register(PhotoOrderingProxy)
class PhotoOrderingAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        return redirect("/admin/galeries/photo-ordering/")
