from django.urls import path
from . import views

urlpatterns = [
    path("", views.FournisseurListCreateView.as_view(), name="fournisseurs"),
    path("<int:pk>/", views.FournisseurDetailView.as_view(), name="fournisseur_detail"),

    # Téléphones
    path("<int:fournisseur_pk>/telephones/", views.FournisseurTelephoneListCreateView.as_view(), name="fournisseur_telephones"),
    path("<int:fournisseur_pk>/telephones/<int:pk>/", views.FournisseurTelephoneDetailView.as_view(), name="fournisseur_telephone_detail"),
]