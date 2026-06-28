from django.urls import path
from . import views

urlpatterns = [
    path("", views.CategorieListCreateView.as_view(), name="categories"),
    path("<int:pk>/", views.CategorieDetailView.as_view(), name="categorie_detail"),
]