from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import Client, ClientTelephone, ClientContactUrgence
from .serializers import (
    ClientSerializer,
    ClientCreateUpdateSerializer,
    ClientTelephoneSerializer,
    ClientContactUrgenceSerializer,
)
from authentification.permissions import EstAdmin, EstAdminOuLecture


class ClientListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Client.objects.prefetch_related(
            "telephones", "contacts_urgence"
        ).all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(telephones__numero__icontains=search)
            ).distinct()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClientCreateUpdateSerializer
        return ClientSerializer

    def perform_create(self, serializer):
        client = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="clients",
            reference=str(client.nom_complet),
            description=f"Client {client.nom_complet} créé.",
            request=self.request,
        )


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.prefetch_related("telephones", "contacts_urgence").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ClientCreateUpdateSerializer
        return ClientSerializer

    def perform_update(self, serializer):
        client = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="clients",
            reference=str(client.nom_complet),
            description=f"Client {client.nom_complet} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        if request.user.role != "admin":
            return Response(
                {"detail": "Suppression réservée à l'administrateur."},
                status=status.HTTP_403_FORBIDDEN
            )
        client = self.get_object()
        if client.ventes.exists():
            return Response(
                {"detail": "Impossible de supprimer : ce client a des ventes liées."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reference = str(client.nom_complet)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="clients",
                reference=reference,
                description=f"Client {reference} supprimé.",
                request=request,
            )
        return response


# --- Téléphones ---

class ClientTelephoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ClientTelephoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientTelephone.objects.filter(client_id=self.kwargs["client_pk"])

    def perform_create(self, serializer):
        client = Client.objects.get(pk=self.kwargs["client_pk"])
        telephone = serializer.save(client=client)
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="clients",
            reference=f"Téléphone {telephone.numero}",
            description=f"Téléphone {telephone.numero} ajouté pour le client {client.nom_complet}.",
            request=self.request,
        )


class ClientTelephoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientTelephoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientTelephone.objects.filter(client_id=self.kwargs["client_pk"])

    def perform_update(self, serializer):
        telephone = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="clients",
            reference=f"Téléphone {telephone.numero}",
            description=f"Téléphone {telephone.numero} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        telephone = self.get_object()
        reference = f"Téléphone {telephone.numero}"
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="clients",
                reference=reference,
                description=f"Téléphone {telephone.numero} supprimé.",
                request=request,
            )
        return response


# --- Contacts d'urgence ---

class ClientContactUrgenceListCreateView(generics.ListCreateAPIView):
    serializer_class = ClientContactUrgenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientContactUrgence.objects.filter(client_id=self.kwargs["client_pk"])
    def perform_update(self, serializer):
        contact = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="clients",
            reference=f"Contact urgence {contact.nom}",
            description=f"Contact urgence {contact.nom} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        contact = self.get_object()
        reference = f"Contact urgence {contact.nom}"
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="clients",
                reference=reference,
                description=f"Contact urgence {contact.nom} supprimé.",
                request=request,
            )
        return response
    def perform_create(self, serializer):
        client = Client.objects.get(pk=self.kwargs["client_pk"])
        contact = serializer.save(client=client)
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="clients",
            reference=f"Contact urgence {contact.nom}",
            description=f"Contact urgence {contact.nom} ajouté pour le client {client.nom_complet}.",
            request=self.request,
        )


class ClientContactUrgenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientContactUrgenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientContactUrgence.objects.filter(client_id=self.kwargs["client_pk"])