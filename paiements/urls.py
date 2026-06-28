from django.urls import path
from . import views

urlpatterns = [
    path("clients/", views.PaiementClientListCreateView.as_view(), name="paiements_clients"),
    path("clients/ajouter/", views.PaiementClientCreateView.as_view(), name="paiement_client_ajouter"),
    path("clients/<int:pk>/supprimer/", views.PaiementClientDeleteView.as_view(), name="paiement_client_supprimer"),
    path("clients/dettes/", views.VentesEnCours.as_view(), name="dettes_clients"),
]