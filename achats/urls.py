from django.urls import path
from . import views

urlpatterns = [
    # Achats
    path("", views.AchatListCreateView.as_view(), name="achats"),
    path("ajouter/", views.AchatCreateView.as_view(), name="achat_ajouter"),
    path("<int:pk>/", views.AchatDetailView.as_view(), name="achat_detail"),
    path("<int:pk>/annuler/", views.AchatAnnulerView.as_view(), name="achat_annuler"),
    path("<int:pk>/supprimer/", views.AchatDeleteView.as_view(), name="achat_supprimer"),
    path("dettes/", views.AchatsEnCours.as_view(), name="dettes_fournisseurs"),

    # Paiements fournisseurs
    path("paiements/", views.PaiementFournisseurListView.as_view(), name="paiements_fournisseurs"),
    path("paiements/ajouter/", views.PaiementFournisseurCreateView.as_view(), name="paiement_fournisseur_ajouter"),
    path("paiements/<int:pk>/supprimer/", views.PaiementFournisseurDeleteView.as_view(), name="paiement_fournisseur_supprimer"),
]