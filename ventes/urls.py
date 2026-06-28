from django.urls import path
from . import views

urlpatterns = [
    path("", views.VenteListCreateView.as_view(), name="ventes"),
    path("<int:pk>/", views.VenteDetailView.as_view(), name="vente_detail"),
    path("<int:pk>/modifier/", views.VenteUpdateView.as_view(), name="vente_modifier"),
    path("<int:pk>/annuler/", views.VenteAnnulerView.as_view(), name="vente_annuler"),
    path("<int:pk>/supprimer/", views.VenteDeleteView.as_view(), name="vente_supprimer"),
    path("ref/<str:reference>/", views.VenteParReferenceView.as_view(), name="vente_par_reference"),
    path("publique/<str:reference>/", views.VentePubliqueView.as_view(), name="vente_publique"),
]