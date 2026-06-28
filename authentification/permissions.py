from rest_framework.permissions import BasePermission


class EstAdmin(BasePermission):
    """Accès réservé aux administrateurs."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class EstAdminOuLecture(BasePermission):
    """Admin : tout. Caissier : lecture seule (GET)."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.role == "admin"