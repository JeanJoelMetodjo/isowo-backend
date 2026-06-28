from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import Produit
from .serializers import ProduitSerializer, ProduitCreateUpdateSerializer
from authentification.permissions import EstAdmin


class ProduitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Produit.objects.select_related(
            "categorie", "fournisseur", "stock"
        ).all()

        search = self.request.query_params.get("search")
        categorie = self.request.query_params.get("categorie")
        actif = self.request.query_params.get("actif")
        alerte = self.request.query_params.get("alerte")

        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(code__icontains=search) |
                Q(marque__icontains=search)
            )
        if categorie:
            queryset = queryset.filter(categorie_id=categorie)
        if actif is not None:
            queryset = queryset.filter(est_actif=actif.lower() == "true")
        if alerte == "true":
            # Produits sous le seuil d'alerte
            from django.db.models import F
            queryset = queryset.filter(stock__quantite__lte=F("seuil_alerte"))

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProduitCreateUpdateSerializer
        return ProduitSerializer

    def perform_create(self, serializer):
        produit = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="produits",
            reference=str(produit.code or produit.nom),
            description=f"Produit {produit.nom} créé.",
            request=self.request,
        )


class ProduitDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produit.objects.select_related("categorie", "fournisseur", "stock").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProduitCreateUpdateSerializer
        return ProduitSerializer

    def perform_update(self, serializer):
        produit = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="produits",
            reference=str(produit.code or produit.nom),
            description=f"Produit {produit.nom} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        produit = self.get_object()
        if request.user.role != "admin":
            return Response(
                {"detail": "Suppression réservée à l'administrateur."},
                status=status.HTTP_403_FORBIDDEN
            )
        if produit.lignes_vente.exists():
            return Response(
                {"detail": "Impossible de supprimer : ce produit a des ventes liées."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reference = str(produit.code or produit.nom)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="produits",
                reference=reference,
                description=f"Produit {produit.nom} supprimé.",
                request=request,
            )
        return response
