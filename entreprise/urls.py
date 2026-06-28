from django.urls import path
from . import views

urlpatterns = [
    path("", views.EntrepriseView.as_view(), name="entreprise"),
]