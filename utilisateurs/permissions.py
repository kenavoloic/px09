from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def photographe_requis(view_func):
    """Décorateur pour restreindre l'accès au photographe"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.est_photographe():
            raise PermissionDenied("Accès réservé au photographe")
        return view_func(request, *args, **kwargs)

    return wrapper


def client_ou_photographe_requis(view_func):
    """Décorateur pour clients et photographe"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Connexion requise")
        if not (request.user.est_client() or request.user.est_photographe()):
            raise PermissionDenied("Accès non autorisé")
        return view_func(request, *args, **kwargs)

    return wrapper


class PhotographeRequisMixin(UserPassesTestMixin):
    """Mixin qui vérifie que l'utilisateur est LE photographe"""

    def test_func(self):
        request = getattr(self, "request", None)
        return bool(
            request and request.user.is_authenticated and request.user.est_photographe()
        )


class ClientRequisMixin(UserPassesTestMixin):
    """Mixin qui vérifie que l'utilisateur est un client"""

    def test_func(self):
        request = getattr(self, "request", None)
        return bool(
            request and request.user.is_authenticated and request.user.est_client()
        )
