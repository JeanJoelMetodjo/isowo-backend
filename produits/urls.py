from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProduitListCreateView.as_view(), name="produits"),
    path("<int:pk>/", views.ProduitDetailView.as_view(), name="produit_detail"),
]