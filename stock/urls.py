from django.urls import path
from . import views

urlpatterns = [
    path("", views.StockListView.as_view(), name="stock"),
    path("mouvements/", views.MouvementStockListView.as_view(), name="mouvements_stock"),
    path("ajustement/", views.AjustementManuelView.as_view(), name="ajustement_stock"),
]