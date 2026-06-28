from django.urls import path
from . import views

urlpatterns = [
    path("", views.HistoriqueListView.as_view(), name="historique"),
    path("stats/", views.HistoriqueStatsView.as_view(), name="historique_stats"),
    path("<int:pk>/", views.HistoriqueDetailView.as_view(), name="historique_detail"),
]