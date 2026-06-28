from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),


    path("admin/", admin.site.urls),
    path("api/auth/", include("authentification.urls")),
    path("api/entreprise/", include("entreprise.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/clients/", include("clients.urls")),
    path("api/fournisseurs/", include("fournisseurs.urls")),
    path("api/produits/", include("produits.urls")),
    path("api/stock/", include("stock.urls")),
    path("api/ventes/", include("ventes.urls")),
    path("api/paiements/", include("paiements.urls")),
    path("api/achats/", include("achats.urls")),
    path("api/prets/", include("prets.urls")),
    path("api/historique/", include("historique.urls")),
    path("api/dashboard/", include("dashboard.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)