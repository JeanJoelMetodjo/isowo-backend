from django.urls import path
from . import views

urlpatterns = [
    path("", views.ClientListCreateView.as_view(), name="clients"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),

    # Téléphones
    path("<int:client_pk>/telephones/", views.ClientTelephoneListCreateView.as_view(), name="client_telephones"),
    path("<int:client_pk>/telephones/<int:pk>/", views.ClientTelephoneDetailView.as_view(), name="client_telephone_detail"),

    # Contacts d'urgence
    path("<int:client_pk>/contacts-urgence/", views.ClientContactUrgenceListCreateView.as_view(), name="client_contacts_urgence"),
    path("<int:client_pk>/contacts-urgence/<int:pk>/", views.ClientContactUrgenceDetailView.as_view(), name="client_contact_urgence_detail"),
]