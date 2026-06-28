from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import Fournisseur, FournisseurTelephone
from .serializers import (
    FournisseurSerializer,
    FournisseurCreateUpdateSerializer,
    FournisseurTelephoneSerializer,
)


class FournisseurListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Fournisseur.objects.prefetch_related("telephones").all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(nom_entreprise__icontains=search) |
                Q(nom_contact__icontains=search) |
                Q(telephones__numero__icontains=search)
            ).distinct()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FournisseurCreateUpdateSerializer
        return FournisseurSerializer

    def perform_create(self, serializer):
        fournisseur = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="fournisseurs",
            reference=str(fournisseur.nom_entreprise),
            description=f"Fournisseur {fournisseur.nom_entreprise} créé.",
            request=self.request,
        )


class FournisseurDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Fournisseur.objects.prefetch_related("telephones").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return FournisseurCreateUpdateSerializer
        return FournisseurSerializer

    def perform_update(self, serializer):
        fournisseur = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="fournisseurs",
            reference=str(fournisseur.nom_entreprise),
            description=f"Fournisseur {fournisseur.nom_entreprise} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        if request.user.role != "admin":
            return Response(
                {"detail": "Suppression réservée à l'administrateur."},
                status=status.HTTP_403_FORBIDDEN
            )
        fournisseur = self.get_object()
        if fournisseur.achats.exists():
            return Response(
                {"detail": "Impossible de supprimer : ce fournisseur a des achats liés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reference = str(fournisseur.nom_entreprise)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="fournisseurs",
                reference=reference,
                description=f"Fournisseur {reference} supprimé.",
                request=request,
            )
        return response


# --- Téléphones ---

class FournisseurTelephoneListCreateView(generics.ListCreateAPIView):
    serializer_class = FournisseurTelephoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FournisseurTelephone.objects.filter(
            fournisseur_id=self.kwargs["fournisseur_pk"]
        )

    def perform_create(self, serializer):
        fournisseur = Fournisseur.objects.get(pk=self.kwargs["fournisseur_pk"])
        telephone = serializer.save(fournisseur=fournisseur)
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="fournisseurs",
            reference=f"Téléphone {telephone.numero}",
            description=f"Téléphone {telephone.numero} ajouté pour le fournisseur {fournisseur.nom_entreprise}.",
            request=self.request,
        )


class FournisseurTelephoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FournisseurTelephoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FournisseurTelephone.objects.filter(
            fournisseur_id=self.kwargs["fournisseur_pk"]
        )

    def perform_update(self, serializer):
        telephone = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="fournisseurs",
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
                module="fournisseurs",
                reference=reference,
                description=f"Téléphone {telephone.numero} supprimé.",
                request=request,
            )
        return response