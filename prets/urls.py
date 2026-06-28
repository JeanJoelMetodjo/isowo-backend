from django.urls import path
from . import views

urlpatterns = [
    # Prêts marchandises
    path("marchandises/", views.PretMarchandiseListCreateView.as_view(), name="prets_marchandises"),
    path("marchandises/ajouter/", views.PretMarchandiseCreateView.as_view(), name="pret_marchandise_ajouter"),
    path("marchandises/<int:pk>/", views.PretMarchandiseDetailView.as_view(), name="pret_marchandise_detail"),
    path("marchandises/<int:pk>/rembourser/", views.RemboursementMarchandiseCreateView.as_view(), name="rembourser_marchandise"),

    # Prêts argent
    path("argent/", views.PretArgentListCreateView.as_view(), name="prets_argent"),
    path("argent/ajouter/", views.PretArgentCreateView.as_view(), name="pret_argent_ajouter"),
    path("argent/<int:pk>/", views.PretArgentDetailView.as_view(), name="pret_argent_detail"),
    path("argent/<int:pk>/rembourser/", views.RemboursementArgentCreateView.as_view(), name="rembourser_argent"),
]