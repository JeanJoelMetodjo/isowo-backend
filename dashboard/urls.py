from django.urls import path
from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("ventes-graphe/", views.DashboardVentesGraphView.as_view(), name="dashboard_ventes_graphe"),
    path("top-produits/", views.DashboardTopProduitsView.as_view(), name="dashboard_top_produits"),
]